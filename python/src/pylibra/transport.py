import grpc

from .grpc.admission_control_pb2_grpc import AdmissionControlStub
from .grpc.get_with_proof_pb2 import UpdateToLatestLedgerRequest
from .grpc.get_with_proof_pb2 import RequestItem
from .grpc.get_with_proof_pb2 import GetAccountStateRequest

from ._types import AccountResource

__all__ = ["LibraNetwork"]


class LibraNetwork:
    def __init__(self, host="ac.testnet.libra.org", port="8000"):
        self._host = host
        self._port = port

    def _get_channel(self):
        return grpc.insecure_channel(self._host + ":" + self._port)

    def getAccount(self, address_hex):
        """Get AccountResource for given address."""
        as_request = GetAccountStateRequest()
        as_request.address = bytes.fromhex(address_hex)

        request = UpdateToLatestLedgerRequest()
        request.requested_items.append(RequestItem(get_account_state_request=as_request))

        with self._get_channel() as channel:
            stub = AdmissionControlStub(channel)
            response = stub.UpdateToLatestLedger(request)
            # TODO: care about version and proof!
            blob = response.response_items[0].get_account_state_response.account_state_with_proof.blob.blob

        return AccountResource.create(blob)
