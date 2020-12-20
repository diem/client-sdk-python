# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import requests, typing, dataclasses, uuid

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from json.decoder import JSONDecodeError

from .payment_command import PaymentCommand

from .types import (
    CommandType,
    CommandRequestObject,
    CommandResponseObject,
    CommandResponseStatus,
    PaymentObject,
    PaymentActorObject,
    PaymentActionObject,
    ErrorCode,
    FieldError,
)
from .error import command_error, protocol_error, Error

from . import jws, http_header
from .. import jsonrpc, diem_types, identifier, utils


DEFAULT_CONNECT_TIMEOUT_SECS: float = 2.0
DEFAULT_TIMEOUT_SECS: float = 5.0


class CommandResponseError(Exception):
    def __init__(self, resp: CommandResponseObject) -> None:
        super().__init__(resp)
        self.resp = resp


@dataclasses.dataclass
class Client:
    my_compliance_key_account_address: diem_types.AccountAddress
    jsonrpc_client: jsonrpc.Client
    hrp: str
    session: requests.Session = dataclasses.field(default_factory=lambda: requests.Session())
    timeout: typing.Tuple[float, float] = dataclasses.field(
        default_factory=lambda: (
            DEFAULT_CONNECT_TIMEOUT_SECS,
            DEFAULT_TIMEOUT_SECS,
        )
    )
    my_compliance_key_account_id: str = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.my_compliance_key_account_id = self.account_id(self.my_compliance_key_account_address)

    def send_command(self, command: PaymentCommand, sign: typing.Callable[[bytes], bytes]) -> CommandResponseObject:
        return self.send_request(
            request_sender_address=command.my_actor_address,
            opponent_account_id=command.opponent_actor_obj().address,
            request_bytes=jws.serialize(command.new_request(), sign),
        )

    def send_request(
        self, request_sender_address: str, opponent_account_id: str, request_bytes: bytes
    ) -> CommandResponseObject:
        base_url, public_key = self.get_base_url_and_compliance_key(opponent_account_id)
        response = self.session.post(
            f"{base_url.rstrip('/')}/v2/command",
            data=request_bytes,
            headers={
                http_header.X_REQUEST_ID: str(uuid.uuid4()),
                http_header.X_REQUEST_SENDER_ADDRESS: request_sender_address,
            },
            timeout=self.timeout,
        )
        if response.status_code not in [200, 400]:
            response.raise_for_status()

        cmd_resp = _deserialize_jws(response.content, CommandResponseObject, public_key, protocol_error)
        if cmd_resp.status == CommandResponseStatus.failure:
            raise CommandResponseError(cmd_resp)
        return cmd_resp

    def process_inbound_request(self, request_sender_address: str, request_bytes: bytes) -> PaymentCommand:
        if not request_sender_address:
            raise protocol_error(ErrorCode.missing_http_header, f"missing {http_header.X_REQUEST_SENDER_ADDRESS}")
        try:
            _, public_key = self.get_base_url_and_compliance_key(request_sender_address)
        except ValueError as e:
            raise protocol_error(ErrorCode.invalid_x_request_sender_address, str(e)) from e

        request = _deserialize_jws(request_bytes, CommandRequestObject, public_key, command_error)
        if request.command_type == CommandType.PaymentCommand:
            self.validate_addresses(request.command.payment, request_sender_address)
            cmd = self.create_inbound_payment_command(request.cid, request.command.payment)
            state = cmd.state()
            if cmd.is_initial():
                self.validate_dual_attestation_limit(cmd.payment.action)
            elif cmd.is_rsend():
                self.validate_recipient_signature(cmd, public_key)
            return cmd

        raise command_error(
            ErrorCode.unknown_command_type,
            f"unknown command_type: {request.command_type}",
        )

    def validate_recipient_signature(self, cmd: PaymentCommand, public_key: Ed25519PublicKey) -> None:
        msg = cmd.travel_rule_metadata_signature_message(self.hrp)
        try:
            public_key.verify(bytes.fromhex(cmd.payment.recipient_signature), msg)
        except (ValueError, InvalidSignature) as e:
            raise command_error(
                ErrorCode.invalid_recipient_signature, str(e), "command.payment.recipient_signature"
            ) from e

    def validate_dual_attestation_limit(self, action: PaymentActionObject) -> None:
        currencies = self.jsonrpc_client.get_currencies()
        limit = self.jsonrpc_client.get_metadata().dual_attestation_limit
        for info in currencies:
            if info.code == action.currency:
                approx_xdx_microdiem_value = info.to_xdx_exchange_rate * action.amount
                if approx_xdx_microdiem_value < limit:
                    raise command_error(
                        ErrorCode.no_kyc_needed,
                        f"payment amount is under travel rule threshold {limit}",
                        "command.payment.action.amount",
                    )
                return
        raise command_error(
            ErrorCode.invalid_field_value,
            f"currency code is invalid: {action.currency}",
            "command.payment.action.currency",
        )

    def validate_addresses(self, payment: PaymentObject, request_sender_address: str) -> None:
        self.validate_actor_address("sender", payment.sender)
        self.validate_actor_address("receiver", payment.receiver)
        self.validate_request_sender_address(request_sender_address, [payment.sender.address, payment.receiver.address])

    def validate_actor_address(self, actor_name: str, actor: PaymentActorObject) -> None:
        try:
            identifier.decode_account(actor.address, self.hrp)
        except ValueError as e:
            raise command_error(
                ErrorCode.invalid_field_value,
                f"could not decode account identifier: {e}",
                f"command.payment.{actor_name}.address",
            ) from e

    def validate_request_sender_address(self, request_sender_address: str, addresses: typing.List[str]) -> None:
        if request_sender_address not in addresses:
            raise command_error(
                ErrorCode.invalid_x_request_sender_address,
                f"address {request_sender_address} is not one of {addresses}",
            )

    def create_inbound_payment_command(self, cid: str, obj: PaymentObject) -> PaymentCommand:
        if self.is_my_account_id(obj.sender.address):
            return PaymentCommand(cid=cid, my_actor_address=obj.sender.address, payment=obj, inbound=True)
        if self.is_my_account_id(obj.receiver.address):
            return PaymentCommand(cid=cid, my_actor_address=obj.receiver.address, payment=obj, inbound=True)

        raise command_error(ErrorCode.unknown_actor_address, "unknown actor addresses: {obj}")

    def is_my_account_id(self, account_id: str) -> bool:
        account_address, _ = identifier.decode_account(account_id, self.hrp)
        if self.my_compliance_key_account_id == self.account_id(account_address):
            return True
        account = self.jsonrpc_client.get_account(account_address)
        if account and account.role.parent_vasp_address:
            return self.my_compliance_key_account_id == self.account_id(account.role.parent_vasp_address)
        return False

    def account_id(self, address: typing.Union[diem_types.AccountAddress, bytes, str]) -> str:
        return identifier.encode_account(utils.account_address(address), None, self.hrp)

    def get_base_url_and_compliance_key(self, account_id: str) -> typing.Tuple[str, Ed25519PublicKey]:
        account_address, _ = identifier.decode_account(account_id, self.hrp)
        return self.jsonrpc_client.get_base_url_and_compliance_key(account_address)


def _deserialize_jws(
    content_bytes: bytes,
    klass: typing.Type[jws.T],
    public_key: Ed25519PublicKey,
    error_fn: typing.Callable[[str, str, typing.Optional[str]], Error],
) -> jws.T:
    try:
        return jws.deserialize(content_bytes, klass, public_key.verify)
    except JSONDecodeError as e:
        raise error_fn(ErrorCode.invalid_json, f"decode json string failed: {e}", None) from e
    except FieldError as e:
        raise error_fn(e.code, f"invalid {klass} json: {e}", e.field) from e
    except InvalidSignature as e:
        raise error_fn(ErrorCode.invalid_jws_signature, f"invalid jws signature: {e}", None) from e
    except ValueError as e:
        raise error_fn(ErrorCode.invalid_jws, f"deserialize JWS bytes failed: {e}", None) from e
