# pyre-strict

import grpc
import typing

from .grpc.admission_control_pb2_grpc import AdmissionControlStub
from .grpc.admission_control_pb2 import Accepted, SubmitTransactionRequest
from .grpc.get_with_proof_pb2 import UpdateToLatestLedgerRequest
from .grpc.get_with_proof_pb2 import RequestItem
from .grpc.get_with_proof_pb2 import GetAccountStateRequest
from .grpc.get_with_proof_pb2 import GetTransactionsRequest, GetAccountTransactionBySequenceNumberRequest

from ._types import AccountResource, SignedTransaction, TransactionUtils


class ClientError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, message: str) -> None:
        self.message = message

    def __repr__(self) -> str:
        return self.message


class SubmitTransactionError(ClientError):
    pass


class LibraNetwork:
    def __init__(self, host: str = "ac.testnet.libra.org", port: str = "8000") -> None:
        self._host: str = host
        self._port: str = port

    def _get_channel(self) -> grpc.Channel:
        return grpc.insecure_channel(self._host + ":" + self._port)

    def getAccount(self, address_hex: str) -> AccountResource:
        """Get AccountResource for given address."""
        address_bytes = bytes.fromhex(address_hex)

        as_request = GetAccountStateRequest()
        as_request.address = address_bytes

        request = UpdateToLatestLedgerRequest()
        request.requested_items.append(RequestItem(get_account_state_request=as_request))

        with self._get_channel() as channel:
            stub = AdmissionControlStub(channel)
            response = stub.UpdateToLatestLedger(request)
            # TODO: care about version and proof!
            blob = response.response_items[0].get_account_state_response.account_state_with_proof.blob.blob
            return AccountResource.create(address_bytes, blob)

    def sendTransaction(self, signed_transaction_bytes: bytes) -> None:
        request = SubmitTransactionRequest()
        request.transaction.txn_bytes = signed_transaction_bytes

        with self._get_channel() as channel:
            stub = AdmissionControlStub(channel)
            response = stub.SubmitTransaction(request)
            ex = None
            if response.HasField("vm_status"):
                ex = SubmitTransactionError(
                    "VM Status, major code %d, sub code %d, message: '%s'."
                    % (response.vm_status.major_status, response.vm_status.sub_status, response.vm_status.message,)
                )
            elif response.HasField("ac_status"):
                if response.ac_status.code != Accepted:
                    ex = SubmitTransactionError(
                        "AC Error, code: %d, msg: %s" % (response.ac_status.code, response.ac_status.message)
                    )
            elif response.HasField("mempool_status"):
                ex = SubmitTransactionError("mempool Status: %s" % response.mempool_status)

            if ex:
                raise ex

    def transactions_by_range(
        self, start_version: int, limit: int, include_events: bool = False
    ) -> typing.List[SignedTransaction]:
        request = UpdateToLatestLedgerRequest()

        tx_req = GetTransactionsRequest()
        tx_req.start_version = start_version
        tx_req.limit = limit
        tx_req.fetch_events = include_events

        request.requested_items.append(RequestItem(get_transactions_request=tx_req))

        with self._get_channel() as channel:
            stub = AdmissionControlStub(channel)
            response = stub.UpdateToLatestLedger(request)
            txs = response.response_items[0].get_transactions_response.txn_list_with_proof
            if not len(txs.transactions):
                return []

            res = []
            version = txs.first_transaction_version.value
            for tx in txs.transactions:
                try:
                    # Proto buffer message here contains a 4 byte prefix
                    tx_blob = tx.transaction[4:]
                    t = TransactionUtils.parse(version, tx_blob)
                    res.append(t)
                except ValueError:
                    # TODO: Unsupported TXN type
                    continue
                finally:
                    version += 1

            return res

    def transaction_by_acc_seq(
        self, addr_hex: str, seq: int, include_events: bool = False
    ) -> typing.Optional[SignedTransaction]:
        request = UpdateToLatestLedgerRequest()

        tx_req = GetAccountTransactionBySequenceNumberRequest()
        tx_req.account = bytes.fromhex(addr_hex)
        tx_req.sequence_number = seq
        tx_req.fetch_events = include_events

        request.requested_items.append(RequestItem(get_account_transaction_by_sequence_number_request=tx_req))

        with self._get_channel() as channel:
            stub = AdmissionControlStub(channel)
            response = stub.UpdateToLatestLedger(request)
            tx = response.response_items[0].get_account_transaction_by_sequence_number_response.transaction_with_proof
            version = tx.version
            tx_blob = tx.transaction.transaction
            try:
                # Proto buffer message here contains a 4 byte prefix
                tx_blob = tx_blob[4:]
                return TransactionUtils.parse(version, tx_blob)
            except ValueError:
                # TODO: Unsupported TXN type
                pass

            return None
