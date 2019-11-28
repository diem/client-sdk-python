from __future__ import print_function
import logging

import grpc

from .proto import admission_control_pb2_grpc
from .proto.get_with_proof_pb2 import UpdateToLatestLedgerRequest
from .proto.get_with_proof_pb2 import RequestItem
from .proto.get_with_proof_pb2 import GetAccountStateRequest


def get_account_state_blob(address_hex, host ="ac.testnet.libra.org", port="8000"):
    """Get Account State Blob for address (hex) . """

    as_request = GetAccountStateRequest()
    as_request.address = bytes.fromhex(address_hex)

    request = UpdateToLatestLedgerRequest()
    request.requested_items.append(RequestItem(get_account_state_request = as_request))

    with grpc.insecure_channel(host + ":" + port) as channel:
        stub = admission_control_pb2_grpc.AdmissionControlStub(channel)
        response = stub.UpdateToLatestLedger(request)
        # TODO: care about version and proof!
        blob = response.response_items[0].get_account_state_response.account_state_with_proof.blob.blob
    return blob
