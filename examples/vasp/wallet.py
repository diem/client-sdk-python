# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from dataclasses import dataclass, field
from http import server
from diem import (
    identifier,
    jsonrpc,
    diem_types,
    stdlib,
    testnet,
    utils,
    LocalAccount,
    offchain,
)
import logging, threading, typing

logger: logging.Logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class User:
    name: str
    subaddresses: typing.List[bytes] = field(default_factory=lambda: [])

    def kyc_data(self) -> offchain.KycDataObject:
        return offchain.individual_kyc_data(
            given_name=self.name,
            surname=f"surname-{self.name}",
            address=offchain.AddressObject(city="San Francisco"),
        )

    def additional_kyc_data(self) -> str:
        return f"{self.name}'s secret"


class ActionResultType(str):
    pass


class ActionResult:
    PASS = ActionResultType("pass")
    REJECT = ActionResultType("reject")
    SOFT_MATCH = ActionResultType("soft_match")
    SENT_ADDITIONAL_KYC_DATA = ActionResultType("sent_additional_kyc_data")
    TXN_EXECUTED = ActionResultType("transaction_executed")
    SEND_REQUEST_SUCCESS = ActionResultType("send_request_success")


BgResult = typing.Tuple[typing.Optional[offchain.action.Action], ActionResultType]


@dataclass
class WalletApp:
    """WalletApp is an example of custodial wallet application"""

    @staticmethod
    def generate(name: str, client: jsonrpc.Client) -> "WalletApp":
        """generate a WalletApp running on testnet"""

        offchain_service_port = offchain.http_server.get_available_port()
        account = testnet.gen_vasp_account(client, f"http://localhost:{offchain_service_port}")
        w = WalletApp(
            name=name,
            jsonrpc_client=client,
            parent_vasp=account,
            offchain_service_port=offchain_service_port,
        )
        w.add_child_vasp()
        return w

    name: str
    jsonrpc_client: jsonrpc.Client
    parent_vasp: LocalAccount
    offchain_service_port: int

    hrp: str = field(default=identifier.TDM)
    saved_commands: typing.Dict[str, offchain.Command] = field(default_factory=lambda: {})
    child_vasps: typing.List[LocalAccount] = field(default_factory=lambda: [])
    users: typing.Dict[str, User] = field(default_factory=lambda: {})
    evaluate_kyc_data_result: typing.Dict[str, ActionResultType] = field(default_factory=lambda: {})
    manual_review_result: typing.Dict[str, ActionResultType] = field(default_factory=lambda: {})
    task_queue: typing.List[typing.Callable[["WalletApp"], BgResult]] = field(default_factory=lambda: [])
    locks: typing.Dict[str, threading.Lock] = field(default_factory=lambda: {})
    compliance_key: Ed25519PrivateKey = field(init=False)
    offchain_client: offchain.Client = field(init=False)

    def __post_init__(self) -> None:
        self.compliance_key = self.parent_vasp.compliance_key
        self.offchain_client = offchain.Client(self.parent_vasp.account_address, self.jsonrpc_client, self.hrp)

    # --------------------- end user interaction --------------------------

    def pay(
        self,
        user_name: str,
        intent_id: str,
        desc: typing.Optional[str] = None,
        original_payment_reference_id: typing.Optional[str] = None,
    ) -> str:
        """make payment from given user account to intent_id"""

        intent = identifier.decode_intent(intent_id, self.hrp)
        command = offchain.PaymentCommand.init(
            self.gen_user_account_id(user_name),
            self.users[user_name].kyc_data(),
            intent.account_id,
            intent.amount,
            intent.currency_code,
            original_payment_reference_id=original_payment_reference_id,
            description=desc,
        )
        self.save_command(command)
        return command.reference_id()

    def gen_intent_id(
        self,
        user_name: str,
        amount: int,
        currency: typing.Optional[str] = testnet.TEST_CURRENCY_CODE,
    ) -> str:
        account_id = self.gen_user_account_id(user_name)
        return identifier.encode_intent(account_id, str(currency), amount)

    # --------------------- offchain integration --------------------------

    def process_inbound_request(
        self, x_request_id: str, request_sender_address: str, request_bytes: bytes
    ) -> typing.Tuple[int, bytes]:
        cid = None
        try:
            inbound_command = self.offchain_client.process_inbound_request(request_sender_address, request_bytes)
            cid = inbound_command.id()
            self.save_command(inbound_command)
            resp = offchain.reply_request(cid)
            code = 200
        except offchain.Error as e:
            logger.exception(e)
            resp = offchain.reply_request(cid if cid else None, e.obj)
            code = 400

        return (code, offchain.jws.serialize(resp, self.compliance_key.sign))

    def run_once_background_job(
        self,
    ) -> typing.Optional[BgResult]:
        if len(self.task_queue) == 0:
            return None
        task = self.task_queue[0]
        ret = task(self)
        self.task_queue.remove(task)
        return ret

    # --------------------- admin --------------------------

    def start_server(self) -> server.HTTPServer:
        return offchain.http_server.start_local(self.offchain_service_port, self.process_inbound_request)

    def add_child_vasp(self) -> None:
        self.child_vasps.append(testnet.gen_child_vasp(self.jsonrpc_client, self.parent_vasp))

    def add_user(self, name: str) -> None:
        self.users[name] = User(name)

    def vasp_balance(self, currency: str = testnet.TEST_CURRENCY_CODE) -> int:
        balance = 0
        for vasp in [self.parent_vasp] + self.child_vasps:
            account = self.jsonrpc_client.must_get_account(vasp.account_address)
            balance += utils.balance(account, currency)
        return balance

    def clear_data(self) -> None:
        self.evaluate_kyc_data_result = {}
        self.manual_review_result = {}
        self.users = {}
        self.saved_commands = {}
        self.task_queue = []
        self.locks = {}

    # -------- offchain business actions ---------------

    def _send_additional_kyc_data(self, command: offchain.Command) -> typing.Tuple[ActionResultType, offchain.Command]:
        command = typing.cast(offchain.PaymentCommand, command)
        account_id = command.my_actor_obj().address
        _, subaddress = identifier.decode_account(account_id, self.hrp)
        if subaddress:
            user = self._find_user_by_subaddress(subaddress)
        else:
            raise ValueError(f"{account_id} has no sub-address")
        new_cmd = command.new_command(additional_kyc_data=user.additional_kyc_data())
        return (ActionResult.SENT_ADDITIONAL_KYC_DATA, new_cmd)

    def _submit_travel_rule_txn(
        self,
        command: offchain.Command,
    ) -> ActionResultType:
        command = typing.cast(offchain.PaymentCommand, command)
        child_vasp = self._find_child_vasp(command.sender_account_address(self.hrp))
        assert command.payment.recipient_signature
        testnet.exec_txn(
            self.jsonrpc_client,
            child_vasp,
            stdlib.encode_peer_to_peer_with_metadata_script(
                currency=utils.currency_code(command.payment.action.currency),
                payee=command.receiver_account_address(self.hrp),
                amount=command.payment.action.amount,
                metadata=command.travel_rule_metadata(self.hrp),
                metadata_signature=bytes.fromhex(command.payment.recipient_signature),
            ),
        )

        return ActionResult.TXN_EXECUTED

    def _evaluate_kyc_data(self, command: offchain.Command) -> typing.Tuple[ActionResultType, offchain.Command]:
        command = typing.cast(offchain.PaymentCommand, command)
        op_kyc_data = command.opponent_actor_obj().kyc_data
        assert op_kyc_data is not None
        ret = self.evaluate_kyc_data_result.get(str(op_kyc_data.given_name), ActionResult.PASS)

        if ret == ActionResult.SOFT_MATCH:
            return (ret, command.new_command(status=offchain.Status.soft_match))
        return (ret, self._kyc_data_result("evaluate key data", ret, command))

    def _manual_review(self, command: offchain.Command) -> typing.Tuple[ActionResultType, offchain.Command]:
        command = typing.cast(offchain.PaymentCommand, command)
        op_kyc_data = command.opponent_actor_obj().kyc_data
        assert op_kyc_data is not None
        ret = self.manual_review_result.get(str(op_kyc_data.given_name), ActionResult.PASS)
        return (ret, self._kyc_data_result("review", ret, command))

    def _kyc_data_result(
        self, action: str, ret: ActionResultType, command: offchain.PaymentCommand
    ) -> offchain.Command:
        if ret == ActionResult.PASS:
            if command.is_receiver():
                return self._send_kyc_data_and_receipient_signature(command)
            return command.new_command(status=offchain.Status.ready_for_settlement)
        return command.new_command(
            status=offchain.Status.abort,
            abort_code=offchain.AbortCode.reject_kyc_data,
            abort_message=f"{action}: {ret}",
        )

    def _send_kyc_data_and_receipient_signature(
        self,
        command: offchain.PaymentCommand,
    ) -> offchain.Command:
        sig_msg = command.travel_rule_metadata_signature_message(self.hrp)
        subaddress = command.receiver_subaddress(self.hrp)
        if subaddress:
            user = self._find_user_by_subaddress(subaddress)
        else:
            raise ValueError(f"could not find receiver subaddress: {command}")

        return command.new_command(
            recipient_signature=self.compliance_key.sign(sig_msg).hex(),
            kyc_data=user.kyc_data(),
            status=offchain.Status.ready_for_settlement,
        )

    # ---------------------- offchain Command ---------------------------

    def _send_request(self, command: offchain.PaymentCommand) -> ActionResultType:
        self.offchain_client.send_command(command, self.compliance_key.sign)
        self._enqueue_follow_up_action(command)
        return ActionResult.SEND_REQUEST_SUCCESS

    def _enqueue_follow_up_action(self, command: offchain.Command) -> None:
        if command.follow_up_action():
            self.task_queue.append(lambda app: app._offchain_business_action(command.reference_id()))

    def _offchain_business_action(self, ref_id: str) -> BgResult:
        command = self.saved_commands[ref_id]
        action = command.follow_up_action()
        if not action:
            raise ValueError(f"no follow up action for the command {command}")
        if action == offchain.Action.SUBMIT_TXN:
            return (action, self._submit_travel_rule_txn(command))
        actions = {
            offchain.Action.EVALUATE_KYC_DATA: self._evaluate_kyc_data,
            offchain.Action.CLEAR_SOFT_MATCH: self._send_additional_kyc_data,
            offchain.Action.REVIEW_KYC_DATA: self._manual_review,
        }
        ret, new_command = actions[action](command)
        self.save_command(new_command)
        # return action and action result for test
        return (action, ret)

    # ---------------------- commands ---------------------------

    def save_command(self, command: offchain.Command) -> None:
        """save command locks prior command by reference id, validate and save new command.

        in a production implementation, the lock should be database / distributed lock to ensure
        atomic process(read and write) command by the reference id.
        """

        lock = self.lock(command.reference_id())
        if not lock.acquire(blocking=False):
            msg = f"command(reference_id={command.reference_id()}) is locked"
            raise offchain.command_error(offchain.ErrorCode.conflict, msg)

        try:
            prior = self.saved_commands.get(command.reference_id())
            if command == prior:
                return
            command.validate(prior)
            self.saved_commands[command.reference_id()] = command
            if command.is_inbound():
                self._enqueue_follow_up_action(command)
            else:  # outbound
                self.task_queue.append(lambda app: app._send_request(command))
        finally:
            lock.release()

    def lock(self, ref_id: str) -> threading.Lock:
        return self.locks.setdefault(ref_id, threading.Lock())

    # ---------------------- users ---------------------------

    def _find_user_by_subaddress(self, subaddress: bytes) -> User:
        for u in self.users.values():
            if subaddress in u.subaddresses:
                return u
        raise ValueError(f"could not find user by subaddress: {subaddress.hex()}, {self.name}")

    def gen_user_account_id(self, user_name: str) -> str:
        subaddress = identifier.gen_subaddress()
        self.users[user_name].subaddresses.append(subaddress)
        return identifier.encode_account(self._available_child_vasp().account_address, subaddress, self.hrp)

    # ---------------------- child vasps ---------------------------

    def _available_child_vasp(self) -> LocalAccount:
        return self.child_vasps[0]

    def _find_child_vasp(self, address: diem_types.AccountAddress) -> LocalAccount:
        for vasp in self.child_vasps:
            if vasp.account_address == address:
                return vasp
        raise ValueError(f"could not find child vasp by address: {address.to_hex()}")
