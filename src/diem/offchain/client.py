# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0


import requests, typing, dataclasses, uuid, math, warnings

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from json.decoder import JSONDecodeError

from .command import Command
from .payment_command import PaymentCommand

from .types import (
    CommandType,
    CommandRequestObject,
    CommandResponseObject,
    CommandResponseStatus,
    PaymentObject,
    PaymentActorObject,
    PaymentActionObject,
    PaymentCommandObject,
    ErrorCode,
    FieldError,
)
from .error import command_error, protocol_error, Error

from . import jws, http_header
from .. import jsonrpc, diem_types, identifier, utils


DEFAULT_CONNECT_TIMEOUT_SECS: float = 2.0
DEFAULT_TIMEOUT_SECS: float = 30.0


class CommandResponseError(Exception):
    def __init__(self, resp: CommandResponseObject) -> None:
        super().__init__(resp)
        self.resp = resp


class InvalidCurrencyCodeError(ValueError):
    pass


class UnsupportedCurrencyCodeError(ValueError):
    pass


@dataclasses.dataclass
class Client:
    """Client for communicating with offchain service.

    Provides outbound and inbound request handlings and convertings between bytes and offchain data types.

    Initialization:
    ```
    >>> from diem import offchain, testnet
    >>>
    >>> jsonrpc_client = testnet.create_client()
    >>> account = testnet.gen_account(client, base_url="http://vasp.com/offchain")
    >>> compliance_key_account_address = account.account_address
    >>> client = offchain.Client(compliance_key_account_address, jsonrpc_client, identifier.TDM)
    ```

    Send command:
    ```
    >>> # for command: offchain.PaymentCommand
    >>> client.send_command(command, account.compliance_key.sign)
    ```

    Pre-process inbound request data:
    ```
    from http import server
    from diem.offchain import X_REQUEST_ID, X_REQUEST_SENDER_ADDRESS

    class Handler(server.BaseHTTPRequestHandler):
        def do_POST(self):
            x_request_id = self.headers[X_REQUEST_ID]
            jws_key_address = self.headers[X_REQUEST_SENDER_ADDRESS]
            length = int(self.headers["content-length"])
            content = self.rfile.read(length)

            command = client.process_inbound_request(jws_key_address, content)
            # validate and save command
            ...

    ```

    See example [Wallet#process_inbound_request](https://diem.github.io/client-sdk-python/examples/vasp/wallet.html#examples.vasp.wallet.WalletApp.process_inbound_request) for full example of how to process inbound request.
    """

    my_compliance_key_account_address: diem_types.AccountAddress
    jsonrpc_client: jsonrpc.Client
    hrp: str
    supported_currency_codes: typing.Optional[typing.List[str]] = dataclasses.field(default=None)
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

    def send_command(self, command: Command, sign: typing.Callable[[bytes], bytes]) -> CommandResponseObject:
        return self.send_request(
            request_sender_address=command.my_address(),
            counterparty_account_id=command.counterparty_address(),
            request_bytes=jws.serialize(command.new_request(), sign),
        )

    def send_request(
        self, request_sender_address: str, counterparty_account_id: str, request_bytes: bytes
    ) -> CommandResponseObject:
        base_url, public_key = self.get_base_url_and_compliance_key(counterparty_account_id)
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

    def process_inbound_request(self, request_sender_address: str, request_bytes: bytes) -> Command:
        """Deprecated

        validate and decode the `request_bytes` into `diem.offchain.command.Command` object.

        This function is split into `deserialize_inbound_request` and `process_inbound_payment_command_request`
        for handling command processing properly in the future when new commands are added.
        """

        warnings.warn(
            "`process_inbound_request` is deprecated, call `deserialize_inbound_request` instead, and then call `process_inbound_payment_command_request` if the inbound request is for `PaymentCommand`"
        )

        request = self.deserialize_inbound_request(request_sender_address, request_bytes)
        return self.process_inbound_payment_command_request(request_sender_address, request)

    def deserialize_inbound_request(self, request_sender_address: str, request_bytes: bytes) -> CommandRequestObject:
        """Validate and decode the `request_bytes` into `diem.offchain.command.CommandRequestObject` object.

        Raises `diem.offchain.error.Error` with `protocol_error` when:

        - `request_sender_address` is not provided.
        - Cannot find on-chain account by the `request_sender_address`.
        - Cannot get base url and public key from the on-chain account found by the `request_sender_address`.
        - `request_bytes` is an invalid JWS message: JWS message format or content is invalid, or signature is invalid.
        - Cannot decode `request_bytes` into `diem.offchain.types.command_types.CommandRequestObject`.
        - Decoded `diem.offchain.types.command_types.CommandRequestObject` is invalid according to DIP-1 data structure requirements.
        """

        if not request_sender_address:
            raise protocol_error(ErrorCode.missing_http_header, f"missing {http_header.X_REQUEST_SENDER_ADDRESS}")
        public_key = self.get_inbound_request_sender_public_key(request_sender_address)
        return _deserialize_jws(request_bytes, CommandRequestObject, public_key, command_error)

    def process_inbound_payment_command_request(
        self, request_sender_address: str, request: CommandRequestObject
    ) -> PaymentCommand:
        """Validate the `PaymentCommand` and returns a command wrapper object for next processing step.

        Raises `diem.offchain.error.Error` with `command_error` when `diem.offchain.types.command_types.CommandRequestObject.command` is `diem.offchain.payment_command.PaymentCommand`:

        - `diem.offchain.types.payment_types.PaymentObject.sender` or `diem.offchain.types.payment_types.PaymentObject.sender`.address is invalid.
        - `request_sender_address` is not sender or receiver actor address.
        - For initial payment object, the `diem.offchain.types.payment_types.PaymentActionObject.amount` is under dual attestation limit (travel rule limit).
        - When receiver actor statis is `ready_for_settlement`, the `recipient_signature` is not set or is invalid (verifying transaction metadata failed).

        """

        if request.command_type != CommandType.PaymentCommand:
            raise command_error(
                ErrorCode.unknown_command_type,
                f"unknown command_type: {request.command_type}",
            )

        payment = typing.cast(PaymentCommandObject, request.command).payment
        self.validate_addresses(payment, request_sender_address)
        cmd = self.create_inbound_payment_command(request.cid, payment)
        if cmd.is_initial():
            self.validate_dual_attestation_limit_by_action(cmd.payment.action)
        elif cmd.is_rsend():
            public_key = self.get_inbound_request_sender_public_key(request_sender_address)
            self.validate_recipient_signature(cmd, public_key)
        return cmd

    def get_inbound_request_sender_public_key(self, request_sender_address: str) -> Ed25519PublicKey:
        """find the public key of the request sender address, raises protocol error if not found or public key is invalid"""

        try:
            _, public_key = self.get_base_url_and_compliance_key(request_sender_address)
        except ValueError as e:
            raise protocol_error(ErrorCode.invalid_http_header, str(e)) from e
        return public_key

    def validate_recipient_signature(self, cmd: PaymentCommand, public_key: Ed25519PublicKey) -> None:
        msg = cmd.travel_rule_metadata_signature_message(self.hrp)
        try:
            sig = cmd.payment.recipient_signature
            if sig is None:
                raise ValueError("recipient_signature is not provided")
            public_key.verify(bytes.fromhex(sig), msg)
        except (ValueError, InvalidSignature) as e:
            raise command_error(
                ErrorCode.invalid_recipient_signature, str(e), "command.payment.recipient_signature"
            ) from e

    def validate_dual_attestation_limit_by_action(self, action: PaymentActionObject) -> None:
        msg = self.is_under_dual_attestation_limit(action.currency, action.amount)
        if msg:
            raise command_error(ErrorCode.no_kyc_needed, msg, "command.payment.action.amount")

    def is_under_dual_attestation_limit(self, currency: str, amount: int) -> typing.Optional[str]:
        currencies = self.jsonrpc_client.get_currencies()
        try:
            self.validate_currency_code(currency, currencies)
        except InvalidCurrencyCodeError as e:
            raise command_error(ErrorCode.invalid_field_value, str(e), "command.payment.action.currency")
        except UnsupportedCurrencyCodeError as e:
            raise command_error(ErrorCode.unsupported_currency, str(e), "command.payment.action.currency")

        limit = self.jsonrpc_client.get_metadata().dual_attestation_limit
        for info in currencies:
            if info.code == currency:
                if _is_under_the_threshold(limit, info.to_xdx_exchange_rate, amount):
                    return "payment amount is %s (rate: %s) under travel rule threshold %s" % (
                        amount,
                        info.to_xdx_exchange_rate,
                        limit,
                    )

    def validate_currency_code(
        self, currency: str, currencies: typing.Optional[typing.List[jsonrpc.CurrencyInfo]] = None
    ) -> None:
        if currencies is None:
            currencies = self.jsonrpc_client.get_currencies()
        currency_codes = list(map(lambda c: c.code, currencies))
        supported_codes = _filter_supported_currency_codes(self.supported_currency_codes, currency_codes)
        if currency not in currency_codes:
            raise InvalidCurrencyCodeError(f"currency code is invalid: {currency}")
        if currency not in supported_codes:
            raise UnsupportedCurrencyCodeError(f"currency code is not supported: {currency}")

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
                ErrorCode.invalid_http_header,
                f"address {request_sender_address} is not one of {addresses}",
            )

    def create_inbound_payment_command(self, cid: str, obj: PaymentObject) -> PaymentCommand:
        if self.is_my_account_id(obj.sender.address):
            return PaymentCommand(cid=cid, my_actor_address=obj.sender.address, payment=obj, inbound=True)
        if self.is_my_account_id(obj.receiver.address):
            return PaymentCommand(cid=cid, my_actor_address=obj.receiver.address, payment=obj, inbound=True)

        raise command_error(ErrorCode.unknown_address, "unknown actor addresses: {obj}")

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


def _filter_supported_currency_codes(
    supported_codes: typing.Optional[typing.List[str]], codes: typing.List[str]
) -> typing.List[str]:
    return list(filter(lambda code: supported_codes is None or code in supported_codes, codes))


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
        raise error_fn(e.code, f"invalid {klass.__name__} json: {e}", e.field) from e
    except InvalidSignature as e:
        raise error_fn(ErrorCode.invalid_jws_signature, f"invalid jws signature: {e}", None) from e
    except ValueError as e:
        raise error_fn(ErrorCode.invalid_jws, f"deserialize JWS bytes failed: {e}", None) from e


def _is_under_the_threshold(limit: int, rate: float, amount: int) -> bool:
    # use ceil of the xdx exchanged amount to ensure a valid amount
    # is not considered as under the threshold because of float number
    # transport or calculation difference comparing with Move module
    # implementation.
    return math.ceil(rate * amount) < limit
