#!/bin/bash
set -euo pipefail

# This file downloads all protobuf file from github libra repo, in order
# to be used to generate GRPC client code.
BRANCH=testnet

FILES="
admission_control/admission-control-proto/src/proto/admission_control.proto
mempool/mempool-shared-proto/src/proto/mempool_status.proto
types/src/proto/access_path.proto
types/src/proto/account_state_blob.proto
types/src/proto/events.proto
types/src/proto/get_with_proof.proto
types/src/proto/language_storage.proto
types/src/proto/ledger_info.proto
types/src/proto/proof.proto
types/src/proto/transaction.proto
types/src/proto/transaction_info.proto
types/src/proto/validator_change.proto
types/src/proto/validator_public_keys.proto
types/src/proto/validator_set.proto
types/src/proto/vm_errors.proto
"

rm -f *.proto || true

for FILE in ${FILES}; do
  curl -q -o "$(basename "${FILE}")" "https://raw.githubusercontent.com/libra/libra/${BRANCH}/${FILE}"
done
