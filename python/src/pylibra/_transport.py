import grpc

from .grpc.admission_control_pb2_grpc import AdmissionControlStub
from .grpc.admission_control_pb2 import AdmissionControlStatusCode, SubmitTransactionRequest, SubmitTransactionResponse
from .grpc.get_with_proof_pb2 import UpdateToLatestLedgerRequest
from .grpc.get_with_proof_pb2 import RequestItem
from .grpc.get_with_proof_pb2 import GetAccountStateRequest

from ._types import AccountResource


class ClientError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return self.message


class SubmitTransactionError(ClientError):
    pass


class LibraNetwork:
    def __init__(self, host="ac.testnet.libra.org", port="8000"):
        self._host = host
        self._port = port

    def _get_channel(self):
        return grpc.insecure_channel(self._host + ":" + self._port)

    def getAccount(self, address_hex):
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

    def sendTransaction(self, signed_transaction_bytes: bytes):
        request = SubmitTransactionRequest()
        request.transaction.txn_bytes = signed_transaction_bytes

        with self._get_channel() as channel:
            stub = AdmissionControlStub(channel)
            response = stub.SubmitTransaction(request)
            ex = None
            print(response)
            if response.HasField("vm_status"):
                ex = SubmitTransactionError(
                    "VM Status, major code %d, sub code %d, message: '%s'."
                    % (response.vm_status.major_status, response.vm_status.sub_status, response.vm_status.message,)
                )
            elif response.HasField("ac_status"):
                if not response.validator_id:
                    ex = SubmitTransactionError("Not validator_id present, txn not accepted!")
                elif response.ac_status.code != AdmissionControlStatusCode.Accepted:
                    ex = SubmitTransactionError(
                        "AC Error, code: %d, msg: %s" % (response.ac_status.code, response.ac_status.message)
                    )
            elif response.HasField("mempool_status"):
                ex = SubmitTransactionError("mempool Status: %s" % response.mempool_status)

            if ex:
                raise ex
