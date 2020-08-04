import time
import typing

import pylibra
import requests
from pylibra import (
    DEFAULT_CONNECT_TIMEOUT_SECS,
    DEFAULT_TIMEOUT_SECS,
    lcs,
    libra_types as libra,
    serde_types as st,
    stdlib,
)

from . import _utils as utils
from ._account import LibraAccount
from ._config import (
    CORE_CODE_ADDRESS,
    DEFAULT_FAUCET_SERVER,
    DEFAULT_JSON_RPC_SERVER,
    DEFAULT_LIBRA_CHAIN_ID,
    DESIGNATED_DEALER_ADDRESS,
    LIBRA_ADDRESS_LEN,
    LIBRA_PRIVATE_KEY_SIZE,
    LIBRA_VM_STATUS_EXECUTED,
    MAX_WAIT_ITERATIONS,
    WAIT_TIME_FOR_TX_STATUS_CHECK,
)
from ._events import (
    LibraEvent,
    LibraReceivedPaymentEvent,
    LibraSentPaymentEvent,
    LibraUnknownEvent,
)
from ._transaction import (
    LibraBlockMetadataTransaction,
    LibraMetadata,
    LibraP2PScript,
    LibraTransaction,
    LibraUnknownTransaction,
    LibraUserTransaction,
    LibraWriteSetTransaction,
)
from ._types import ChainId, LibraLedgerState, SubmitTransactionError, TxStatus
from .json_rpc.request import (
    InvalidServerResponse,
    JsonRpcBatch,
    JsonRpcClient,
    JsonRpcResponse,
)
from .json_rpc.types import (
    AccountStateResponse,
    BlockMetadataTransaction,
    CurrencyInfo,
    JsonRpcError,
    ReceivedPaymentEvent,
    SentPaymentEvent,
    TransactionResponse,
    UnknownEvent,
    UnknownTransaction,
    UserTransaction,
    WriteSetTransaction,
)


class LibraClient:
    def __init__(
        self,
        server: str = DEFAULT_JSON_RPC_SERVER,
        faucet: str = DEFAULT_FAUCET_SERVER,
        session: typing.Optional[requests.Session] = None,
        timeout: typing.Optional[
            typing.Union[float, typing.Tuple[float, float]]
        ] = None,
        ledger_state: typing.Optional[LibraLedgerState] = None,
    ) -> None:
        if not session:
            self._session = requests.Session()
            self._should_close_session = True
        else:
            self._session = session
            self._should_close_session = False

        if not timeout:
            self._timeout = (DEFAULT_CONNECT_TIMEOUT_SECS, DEFAULT_TIMEOUT_SECS)
        else:
            self._timeout = timeout

        # Both Faucet & Json-Rpc by default will work on testnet
        self._faucet = faucet
        self._libra_network = pylibra.LibraNetwork(session=self._session)

        self._json_rpc_client = JsonRpcClient(server, self._session, self._timeout)

        # ledger_state
        if not ledger_state:
            self._ledger_state = LibraLedgerState(DEFAULT_LIBRA_CHAIN_ID, 0, 0)
        else:
            self._ledger_state = ledger_state

    def __del__(self):
        if self._should_close_session:
            self._session.close()

    def mint_and_wait(
        self, authkey_hex: str, amount: int, identifier: str = "LBR"
    ) -> None:
        if len(authkey_hex) != 64:
            raise ValueError("Invalid argument for authkey")

        if amount <= 0:
            raise ValueError("Invalid argument for amount")

        designated_dealer_next_sequence_num: int = self._mint(
            authkey_hex, amount, identifier
        )

        # TODO (ssinghaldev) T69027015 log later instead of just re-raising
        try:
            self._wait_for_transaction_to_complete(
                DESIGNATED_DEALER_ADDRESS, designated_dealer_next_sequence_num
            )
        except pylibra.ClientError as e:
            raise e

    def submit_transaction_and_wait(self, signed_transaction_bytes: bytes) -> TxStatus:
        # checking the signed_transaction_bytes
        # 1. len
        # 2. deserializing & making sure it matched the type libra.SignedTransaction
        if len(signed_transaction_bytes) == 0:
            raise ValueError("Invalid argument for signed_transaction_bytes")

        signed_tx, remaining_bytes = lcs.deserialize(
            signed_transaction_bytes, libra.SignedTransaction
        )
        if remaining_bytes:
            raise ValueError(
                f"Invalid signed_transaction_bytes: {signed_transaction_bytes}"
            )

        # submitting the tx
        try:
            self.submit_transaction(signed_transaction_bytes)
        except pylibra.ClientError as e:
            raise SubmitTransactionError(f"Error in submitting transaction: {e}")

        # waiting for tx execution & getting the final status
        return self.wait_for_transaction_execution(signed_tx)

    def submit_transaction(self, signed_transaction_bytes: bytes) -> None:
        batch: JsonRpcBatch = JsonRpcBatch()
        batch.add_submit_request(signed_transaction_bytes.hex())

        try:
            batch_resp: JsonRpcResponse = self._json_rpc_client.execute(batch)
        except InvalidServerResponse as e:
            raise pylibra.ClientError(f"Invalid Server Response: {e}")

        submit_resp = batch_resp.responses[0]
        if isinstance(submit_resp, JsonRpcError):
            raise pylibra.ClientError(
                f"Received error response: {repr(submit_resp)} from server"
            )

    def wait_for_transaction_execution(
        self, signed_tx: libra.SignedTransaction
    ) -> TxStatus:
        """Function to get the final status of an account transaction

        This func will wait-loop till the expiration timestamp of transaction to get its status.

        Args:
            signed_tx (libra.SignedTransaction): Libra Signed Transaction

        Return:
            TxStatus: Status of the Transaction
        """
        raw_txn: libra.RawTransaction = signed_tx.raw_txn

        sender_account_addr = utils.make_addr_str(raw_txn.sender)
        tx_seq = int(raw_txn.sequence_number)
        tx_expiration_timestamp_secs = int(raw_txn.expiration_timestamp_secs)

        # Let us initialize it with UNKNOWN status
        current_status = TxStatus.UNKNOWN
        is_expired = False

        # This format of this type of looping is intentional. We wish to check one-time final status even after the expiry of transaction
        # The reason being that status could change b/w time we last checked & breaking out due to expiration
        # This format implicitly does that as one can see we are checking tx_status one last time even after the exipry
        while not is_expired:
            current_timestamp_secs = int(time.time())
            is_expired = current_timestamp_secs >= tx_expiration_timestamp_secs

            current_status = self._get_current_transaction_status(
                sender_account_addr, tx_seq, signed_tx
            )

            # if we know for sure whether the tx is success or failure or is_expired, then break from the loop,
            if (
                current_status == TxStatus.SUCCESS
                or current_status == TxStatus.EXECUTION_FAIL
                or is_expired
            ):
                break

            time.sleep(WAIT_TIME_FOR_TX_STATUS_CHECK)

        return current_status

    def _get_current_transaction_status(
        self, account_addr: str, seq_num: int, signed_tx: libra.SignedTransaction
    ) -> TxStatus:
        # Network Error or Json-RPC error response
        try:
            tx_info = self.get_account_transaction(account_addr, seq_num, False)
        except pylibra.ClientError:
            return TxStatus.FETCH_STATUS_FAIL

        # if there are no txs
        if not tx_info:
            return TxStatus.EXPIRED

        # tx execution failed or tx is not the one which is submitted
        if (
            tx_info.vm_status != LIBRA_VM_STATUS_EXECUTED
            or not self._verify_user_transaction(
                typing.cast(LibraUserTransaction, tx_info), signed_tx
            )
        ):
            return TxStatus.EXECUTION_FAIL

        return TxStatus.SUCCESS

    def get_account(
        self,
        account_address: str,
        minimum_blockchain_timestamp_usecs: typing.Optional[int] = None,
    ) -> typing.Optional[LibraAccount]:
        """Function to get LibraAccount given the account address

        Args:
            account_address (typing.List[str]):account address

        Returns:
            typing.Optional[typing.Any]: LibraAccount or None if the account doesn't exist.

        Raises:
            ClientError: if received JsonRpcError in response from server

        """
        batch: JsonRpcBatch = JsonRpcBatch()
        batch.add_get_account_request(account_address)

        batch_resp = self._execute_and_update_ledger_state(
            batch, minimum_blockchain_timestamp_usecs
        )

        accnt_state_resp = batch_resp.responses[0]
        if accnt_state_resp is None:  # account doesn't exist
            return None

        if isinstance(accnt_state_resp, AccountStateResponse):
            return LibraAccount(account_address, accnt_state_resp)

    def transfer_coin_peer_to_peer(
        self,
        sender_private_key: str,
        sender_sequence: int,
        currency_identifier: str,
        receiver: str,
        amount: int,
        metadata: bytes = b"",
        metadata_signature: bytes = b"",
        *ignore: typing.Any,
        max_gas_amount: int = 1_000_000,
        gas_unit_price: int = 0,
        gas_identifier: str = "LBR",
        expiration_timestamp_secs: int = int(time.time()) + 5 * 60,
    ) -> TxStatus:
        # Args Verification
        if len(bytes.fromhex(sender_private_key)) != LIBRA_PRIVATE_KEY_SIZE:
            raise ValueError("Incorrect sender private key")

        if len(bytes.fromhex(receiver)) != LIBRA_ADDRESS_LEN:
            raise ValueError("Incorrect receiver address")

        if sender_sequence < 0:
            raise ValueError("Incorrect sender sequence")

        if amount <= 0:
            raise ValueError("amount to transfer should be positive")

        if not (
            (len(metadata) == 0 and len(metadata_signature) == 0)
            or (len(metadata) > 0 and len(metadata_signature) > 0)
        ):
            raise ValueError(
                "Either both metadata and metadata signatures should be empty or both should be non-empty"
            )

        # create txn_params
        tx_params = self._create_tx_params_dict(
            sender_private_key,
            sender_sequence,
            max_gas_amount,
            gas_unit_price,
            gas_identifier,
            expiration_timestamp_secs,
        )

        ## create type tag for move script
        type_tag = self._create_currency_type_tag(currency_identifier)

        ## create script
        tx_script: libra.Script = stdlib.encode_peer_to_peer_with_metadata_script(
            currency=type_tag,
            payee=utils.make_libra_account_address(receiver),
            amount=st.uint64(amount),
            metadata=metadata,
            metadata_signature=metadata_signature,
        )

        # create signed_tx_bytes
        signed_tx_bytes = self._get_signed_tx_bytes(tx_params, tx_script)

        # submit the transaction bytes
        return self.submit_transaction_and_wait(signed_tx_bytes)

    def add_currency_to_account(
        self,
        sender_private_key: str,
        sender_sequence: int,
        currency_to_add: str,
        *ignore: typing.Any,
        max_gas_amount: int = 1_000_000,
        gas_unit_price: int = 0,
        gas_identifier: str = "LBR",
        expiration_timestamp_secs: int = int(time.time()) + 5 * 60,
    ) -> TxStatus:
        # Args Verification
        if len(bytes.fromhex(sender_private_key)) != LIBRA_PRIVATE_KEY_SIZE:
            raise ValueError("Incorrect sender private key")

        if sender_sequence < 0:
            raise ValueError("Incorrect sender sequence")

        # create txn_params
        tx_params = self._create_tx_params_dict(
            sender_private_key,
            sender_sequence,
            max_gas_amount,
            gas_unit_price,
            gas_identifier,
            expiration_timestamp_secs,
        )

        ## create type tag for move script
        type_tag = self._create_currency_type_tag(currency_to_add)

        ## create script
        tx_script: libra.Script = stdlib.encode_add_currency_to_account_script(
            currency=type_tag
        )

        # create signed_tx_bytes
        signed_tx_bytes = self._get_signed_tx_bytes(tx_params, tx_script)

        # submit the transaction bytes
        return self.submit_transaction_and_wait(signed_tx_bytes)

    def rotate_dual_attestation_info(
        self,
        sender_private_key: str,
        sender_sequence: int,
        new_url: str,
        new_key: bytes,
        *ignore: typing.Any,
        max_gas_amount: int = 1_000_000,
        gas_unit_price: int = 0,
        gas_identifier: str = "LBR",
        expiration_timestamp_secs: int = int(time.time()) + 5 * 60,
    ) -> TxStatus:
        # Args Verification
        if len(bytes.fromhex(sender_private_key)) != LIBRA_PRIVATE_KEY_SIZE:
            raise ValueError("Incorrect sender private key")

        if sender_sequence < 0:
            raise ValueError("Incorrect sender sequence")

        # create txn_params
        tx_params = self._create_tx_params_dict(
            sender_private_key,
            sender_sequence,
            max_gas_amount,
            gas_unit_price,
            gas_identifier,
            expiration_timestamp_secs,
        )

        ## create script
        tx_script: libra.Script = stdlib.encode_rotate_dual_attestation_info_script(
            bytes(new_url, "utf-8"), new_key
        )

        # create signed_tx_bytes
        signed_tx_bytes = self._get_signed_tx_bytes(tx_params, tx_script)

        # submit the transaction bytes
        return self.submit_transaction_and_wait(signed_tx_bytes)

    def get_account_transaction(
        self,
        account_address: str,
        seq: int,
        inlcude_events: bool,
        minimum_blockchain_timestamp_usecs: typing.Optional[int] = None,
    ) -> typing.Optional[LibraTransaction]:
        batch: JsonRpcBatch = JsonRpcBatch()
        batch.add_get_trasaction_by_accnt_seq_request(
            account_address, seq, inlcude_events
        )

        batch_resp = self._execute_and_update_ledger_state(
            batch, minimum_blockchain_timestamp_usecs
        )

        tx_resp = batch_resp.responses[0]
        if tx_resp is None:  # tx doesn't exist
            return None

        if isinstance(tx_resp, TransactionResponse):
            if isinstance(tx_resp.transaction, UserTransaction):
                return typing.cast(LibraTransaction, LibraUserTransaction(tx_resp))

    def get_transactions(
        self,
        start_version: int,
        limit: int,
        include_events: bool,
        minimum_blockchain_timestamp_usecs: typing.Optional[int] = None,
    ) -> typing.List[LibraTransaction]:
        batch: JsonRpcBatch = JsonRpcBatch()
        batch.add_get_transactions_by_range_request(
            start_version, limit, include_events
        )

        batch_resp = self._execute_and_update_ledger_state(
            batch, minimum_blockchain_timestamp_usecs
        )

        tx_resp = batch_resp.responses[0]

        transactions: typing.List[LibraTransaction] = []
        for tx in tx_resp:
            if isinstance(tx.transaction, UserTransaction):
                transactions.append(
                    typing.cast(LibraTransaction, LibraUserTransaction(tx))
                )
            elif isinstance(tx.transaction, BlockMetadataTransaction):
                transactions.append(
                    typing.cast(LibraTransaction, LibraBlockMetadataTransaction(tx))
                )
            elif isinstance(tx.transaction, WriteSetTransaction):
                transactions.append(
                    typing.cast(LibraTransaction, LibraWriteSetTransaction(tx))
                )
            elif isinstance(tx.transaction, UnknownTransaction):
                transactions.append(
                    typing.cast(LibraTransaction, LibraUnknownTransaction(tx))
                )
            else:
                raise pylibra.ClientError(
                    f"Unrecognized transaction: {repr(tx)} response from server"
                )

        return transactions

    def get_account_sent_events(
        self,
        account_addr: str,
        start_seq: int,
        limit: int,
        minimum_blockchain_timestamp_usecs: typing.Optional[int] = None,
    ) -> typing.List[LibraSentPaymentEvent]:
        # Get acount sent event stream key
        sent_events_key = self._get_event_key(account_addr, "sent")

        # get_events with sent events stream key
        return self._get_events_by_type(
            sent_events_key,
            start_seq,
            limit,
            "sent",
            minimum_blockchain_timestamp_usecs,
        )

    def get_account_received_events(
        self,
        account_addr: str,
        start_seq: int,
        limit: int,
        minimum_blockchain_timestamp_usecs: typing.Optional[int] = None,
    ) -> typing.List[LibraReceivedPaymentEvent]:
        # Get acount received event stream key
        received_events_key = self._get_event_key(account_addr, "received")

        # get_events with received events stream key
        return self._get_events_by_type(
            received_events_key,
            start_seq,
            limit,
            "received",
            minimum_blockchain_timestamp_usecs,
        )

    def get_currencies(
        self, minimum_blockchain_timestamp_usecs: typing.Optional[int] = None
    ) -> typing.List[CurrencyInfo]:
        batch: JsonRpcBatch = JsonRpcBatch()
        batch.add_get_currencies_request()

        batch_resp = self._execute_and_update_ledger_state(
            batch, minimum_blockchain_timestamp_usecs
        )

        curr_resp = batch_resp.responses[0]
        return curr_resp.currencies_info

    def get_metadata(
        self,
        version: typing.Optional[int] = None,
        minimum_blockchain_timestamp_usecs: typing.Optional[int] = None,
    ) -> LibraMetadata:
        batch: JsonRpcBatch = JsonRpcBatch()
        batch.add_get_metadata_request(version)

        batch_resp = self._execute_and_update_ledger_state(
            batch, minimum_blockchain_timestamp_usecs
        )

        metadata_resp = batch_resp.responses[0]
        return LibraMetadata(metadata_resp)

    def _mint(self, authkey_hex: str, amount: int, identifier: str = "LBR") -> int:
        """Mint coins from faucet & return TREASURY's next sequence number"""
        try:
            response = self._session.post(
                self._faucet,
                params={
                    "amount": amount,
                    "auth_key": authkey_hex,
                    "currency_code": identifier,
                },
                timeout=self._timeout,
            )
            response.raise_for_status()

            if response.text:
                return int(response.text)

        except requests.RequestException as e:
            raise pylibra.ClientError(f"Unable to mint coins. Error: {e}")

        return 0

    # [TODO] Take timeout as a param from user
    def _wait_for_transaction_to_complete(self, address_hex: str, seq: int) -> None:
        max_iterations: int = MAX_WAIT_ITERATIONS
        for _ in range(max_iterations):
            # [TODO] this should call our own function instead of pylibra
            # Have to change when we implement it
            try:
                tx, _ = self._libra_network.transaction_by_acc_seq(
                    address_hex, seq, False
                )
            except pylibra.ClientError:
                # Can be a Network Error or Error response from Server
                # Retry till the timeout
                # [TODO] log the error when implement logging
                tx = None

            # TODO (ssinghaldev) T69027125 log later instead of just re-raising
            if tx:
                if (
                    tx.vm_status != 4001
                ):  # [TODO] Should define a enum class for status codes
                    raise pylibra.ClientError(
                        f"Transaction failed to execute. Status Code: {tx.vm_status}"
                    )

                return

            time.sleep(1)  # 1s

        raise pylibra.ClientError("Waiting for transaction execution timed out!!")

    def _verify_user_transaction(
        self, tx_info: LibraUserTransaction, signed_tx: libra.SignedTransaction
    ) -> bool:
        # Check Public Key
        if not tx_info.public_key == signed_tx.authenticator.public_key.value:
            return False

        # Check Signature
        if not tx_info.signature == signed_tx.authenticator.signature.value:
            return False

        # if tx is P2P, verify sender, receiver, amount
        if isinstance(tx_info.script, LibraP2PScript):
            return self._verify_p2p_transaction(tx_info, signed_tx)

        return True

    def _verify_p2p_transaction(
        self, tx_info: LibraUserTransaction, signed_tx: libra.SignedTransaction
    ) -> bool:

        # to avoid pyre errors
        script = typing.cast(LibraP2PScript, tx_info.script)

        # Check sender, receiver, transfer amount
        return (
            tx_info.sender.hex() == utils.make_addr_str(signed_tx.raw_txn.sender)
            and script.receiver == utils.extract_receiver_if_any(signed_tx)
            and script.amount == utils.extract_amount_if_any(signed_tx)
        )

    def _create_tx_params_dict(
        self,
        sender_private_key: str,
        sender_sequence: int,
        max_gas_amount: int,
        gas_unit_price: int,
        gas_identifier: str,
        expiration_timestamp_secs: int,
    ) -> typing.Dict[str, typing.Any]:
        sender_account_key = pylibra.AccountKeyUtils.from_private_key(
            bytes.fromhex(sender_private_key)
        )

        return {
            "sender_private_key": sender_private_key,
            "sender_account_key": sender_account_key,
            "sender_sequence": sender_sequence,
            "max_gas_amount": max_gas_amount,
            "gas_unit_price": gas_unit_price,
            "gas_identifier": gas_identifier,
            "expiration_timestamp_secs": expiration_timestamp_secs,
        }

    def _create_currency_type_tag(self, currency: str) -> libra.TypeTag:
        return libra.TypeTag__Struct(
            libra.StructTag(
                address=utils.make_libra_account_address(CORE_CODE_ADDRESS),
                module=libra.Identifier(currency),
                name=libra.Identifier(currency),
                type_params=[],
            )
        )

    def _get_signed_tx_bytes(
        self, tx_params: typing.Dict[str, typing.Any], tx_script: libra.Script
    ):
        ## create payload object
        tx_payload: libra.TransactionPayload = libra.TransactionPayload__Script(
            tx_script
        )

        # create RawTransaction
        raw_tx: libra.RawTransaction = self._create_raw_txn(tx_params, tx_payload)

        # create SignedTransaction
        signed_tx: libra.SignedTransaction = self._create_signed_txn(
            raw_tx, tx_params["sender_account_key"]
        )

        # serialize signned_txn
        signed_tx_bytes: bytes = lcs.serialize(signed_tx, libra.SignedTransaction)

        return signed_tx_bytes

    def _create_raw_txn(
        self,
        tx_params: typing.Dict[str, typing.Any],
        tx_payload: libra.TransactionPayload,
    ) -> libra.RawTransaction:
        return libra.RawTransaction(
            utils.make_libra_account_address(
                tx_params["sender_account_key"].address.hex()
            ),
            st.uint64(tx_params["sender_sequence"]),
            tx_payload,
            st.uint64(tx_params["max_gas_amount"]),
            st.uint64(tx_params["gas_unit_price"]),
            tx_params["gas_identifier"],
            st.uint64(tx_params["expiration_timestamp_secs"]),
            # TODO (ssinghaldev) Change this to chain-id which will be stored in ledger state in LibraClient
            libra.ChainId(value=st.uint8(ChainId.TESTNET)),
        )

    def _create_signed_txn(
        self, raw_txn: libra.RawTransaction, account_key: pylibra.AccountKey
    ) -> libra.SignedTransaction:
        # LCS of the Raw Transaction
        raw_tx_bytes: bytes = lcs.serialize(raw_txn, libra.RawTransaction)

        # Adding seed to LCS bytes
        raw_tx_bytes_hash = utils.add_seed_to_raw_tx_bytes(raw_tx_bytes)

        # Signing the resulting bytes
        signature = utils.ed25519_sign(
            utils.ed25519_private_key_from_bytes(account_key.private_key),
            raw_tx_bytes_hash,
        )

        # Assembling them in the Struct
        return libra.SignedTransaction(
            raw_txn=raw_txn,
            authenticator=libra.TransactionAuthenticator__Ed25519(
                public_key=libra.Ed25519PublicKey(value=account_key.public_key),
                signature=libra.Ed25519Signature(value=signature),
            ),
        )

    def _get_event_key(self, account_addr: str, type: str) -> str:
        account_state: typing.Optional[LibraAccount] = self.get_account(account_addr)

        if account_state is None:
            raise ValueError(f"account: {account_addr} is not present on chain")

        if type == "sent":
            return account_state.sent_events_key
        elif type == "received":
            return account_state.received_events_key
        else:
            raise ValueError("fInvalid event key type: {type} requested")

    def _get_events_by_type(
        self,
        event_key: str,
        start_seq: int,
        limit: int,
        event_type: typing.Optional[str] = None,
        minimum_blockchain_timestamp_usecs: typing.Optional[int] = None,
    ) -> typing.List[typing.Any]:
        """ Function to get events of a particular type """

        batch: JsonRpcBatch = JsonRpcBatch()
        batch.add_get_events_request(event_key, start_seq, limit)

        batch_resp = self._execute_and_update_ledger_state(
            batch, minimum_blockchain_timestamp_usecs
        )

        events_resp = batch_resp.responses[0]

        # If there is no event_type, then return all events
        if not event_type:
            event_data_cls = [SentPaymentEvent, ReceivedPaymentEvent, UnknownEvent]
            libra_event_cls = LibraEvent

        if event_type == "sent":
            event_data_cls = [SentPaymentEvent]
            libra_event_cls = LibraSentPaymentEvent
        elif event_type == "received":
            event_data_cls = [ReceivedPaymentEvent]
            libra_event_cls = LibraReceivedPaymentEvent
        elif event_type == "unknown":
            event_data_cls = [UnknownEvent]
            libra_event_cls = LibraUnknownEvent
        else:
            raise ValueError("fInvalid event type: {type} requested")

        events = []
        for event in events_resp:
            if type(event.data) not in event_data_cls:
                raise pylibra.ClientError(
                    f"Invalid event: {repr(event)} received\n"
                    f"Expected event type: {event_data_cls} Received event type: {type(event.data)}"
                )

            events.append(libra_event_cls(event))

        return events

    def _execute_and_update_ledger_state(
        self, batch_request, minimum_blockchain_timestamp_usecs
    ):
        # execute the batch request
        try:
            batch_resp: JsonRpcResponse = self._json_rpc_client.execute(batch_request)
        except InvalidServerResponse as e:
            raise pylibra.ClientError(f"Invalid Server Response: {e}")

        # Check for json-rpc error
        if isinstance(batch_resp.responses[0], JsonRpcError):
            raise pylibra.ClientError(
                f"Received error response: {repr(batch_resp.responses[0])} from server"
            )

        # check whether the chain_id matches & response is not stale
        try:
            utils.validate_ledger_state(
                self._ledger_state,
                LibraLedgerState(
                    chain_id=batch_resp.chain_id,
                    blockchain_version=batch_resp.version,
                    blockchain_timestamp_usecs=batch_resp.timestamp_usecs,
                ),
                minimum_blockchain_timestamp_usecs,
            )
        except ValueError as e:
            raise pylibra.ClientError(str(e))

        # update ledger_state
        self._update_ledger_state(batch_resp.version, batch_resp.timestamp_usecs)

        # return the response for further processing
        return batch_resp

    def _update_ledger_state(self, version: int, timestamp_usecs: int) -> None:
        self._ledger_state.blockchain_version = version
        self._ledger_state.blockchain_timestamp_usecs = timestamp_usecs
