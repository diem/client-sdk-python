This file is a checklist of requirement & technical details for a Diem client SDK implementation.

# Basics

- [x] module structure:
  - diem
    - Client: JSON-RPC APIs interface, should support application to do easy mock / stub development.
    - jsonrpc: jsonrpc client interface, include plain data classes / structs defined in Diem JSON-RPC SPEC document.
      - types: data transfer object types for jsonrpc client, should match server side JSON-RPC spec data types.
    - stdlib: move stdlib script utils.
    - testnet: testnet utils, should include FaucetService for handling testnet mint.
    - diem_types: Diem onchain data structure types.
    - utils:
      - signing
      - sha3 hashing, address parsing and converting, hex encoding / decoding
      - [DIP-4] transaction metadata
      - [DIP-5] intent identifier, account identifier
- [ ] JSON-RPC 2.0 Spec:
  - spec version validation.
  - batch requests and responses handling.
- [x] JSON-RPC client error handling should distinguish the following 3 type errors:
  - Transport layer error, e.g. HTTP call failure.
  - JSON-RPC protocol error: e.g. server responds to non json data, or can't be parsed into [Diem JSON-RPC SPEC][1] defined data structure, or missing result & error field.
  - JSON-RPC error: error returned from server.
- [x] https.
- [ ] Client connection pool.
- [x] Handle stale responses:
  - [x] client tracks latest server response block version and timestamp, raise error when received server response contains stale version / timestamp.
    - [x] last known blockchain version >= response version: when connecting to a cluster of fullnodes, it is possible some fullnodes are behind the head couple versions.
    - [x] last known blockchain timestamp >= response timestamp.
  - [x] parse and use diem_chain_id, diem_ledger_version and diem_ledger_tiemstamp in the JSONRPC response.
- [x] Parsing and gen Diem Account Identifier (see [DIP-5][2])
  - bech32 addresses/subaddresses support
- [x] language specific standard release publish: e.g. java maven central repo, python pip
- [x] Multi-network: initialize Client with chain id, JSON-RPC server URL
- [x] Handle unsigned int64 data type properly
- [x] Validate server chain id: client should be initialized with chain id and validate server response chain id is the same.
- [x] Validate input parameters, e.g. invalid account address: "kkk". Should return / raise InvalidArgumentError.
- [ ] Send request with "client sdk name / version" as HTTP User-Agent: this is for server to recognize client sdk version, so that server can block a specific client version if we found unacceptable bugs.
- [x] Decode transaction script bytes

# [DIP-4][7] support

- [x] Non-custodial to custodial transaction
- [x] Custodial to non-custodial transaction
- [x] Custodial to Custodial transaction
- [x] Refund

# [DIP-5][2] support

- [x] Encode and decode account identifier
- [x] Encode and decode intent identifier

# Read from Blockchain

- [x] Get metadata
- [x] Get currencies
- [x] Get events
- [x] Get transactions
- [x] Get account
- [x] Get account transaction
- [x] Get account transactions
- [x] Get account events
- [x] Handle error response
- [x] Serialize result JSON to typed data structure
- [x] Forward compatible: ignore unknown fields for
- [x] Backward compatible: new fields are optional

# Submit Transaction

- [x] Submit [p2p transfer][3] transaction
- [x] Submit other [Move Stdlib scripts][4]
- [x] waitForTransaction(accountAddress, sequence, transcationHash, expirationTimeSec, timeout):
  - for given signed transaction sender address, sequence number, expiration time (or 5 sec timeout) to wait and validate execution result is executed, otherwise return/raise an error / flag to tell it is not executed.
  - when signedTransactionHash validation failed, it should return / raise TransactionSequenceNumberConflictError
  - when transaction execution vm_status is not "executed", it should return / raise TransactionExecutionFailure
  - when transaction expired, it should return / raise TransactionExpiredError: compare the transaction expirationTimeSec with response latest ledger timestamp. If response latest ledger timestamp >= transaction expirationTimeSec, then we are sure the transaction will never be executed successfully.
    - Note: response latest ledger timestamp unit is microsecond, expirationTimeSec's unit is second.

# Testnet support

- [x] Generate ed25519 private key, derive ed25519 public keys from private key.
- [x] Generate Single auth-keys
- [ ] Generate MultiSig auth-keys
- [x] Mint coins through [Faucet service][6]

See [doc][5] for above concepts.

# Examples

- [x] [p2p transfer examples](https://github.com/diem/lip/blob/master/lips/lip-4.md#transaction-examples)
- [x] refund p2p transfer example
- [x] create childVASP example
- [x] Intent identifier encoding, decoding example

# Nice to have

- [ ] Async client
- [ ] CLI connects to testnet for trying out features.

[1]: https://github.com/diem/diem/blob/master/json-rpc/json-rpc-spec.md "Diem JSON-RPC SPEC"
[2]: https://github.com/diem/lip/blob/master/lips/lip-5.md "Address formatting"
[3]: https://github.com/diem/diem/blob/master/language/stdlib/transaction_scripts/doc/peer_to_peer_with_metadata.md "P2P Transafer"
[4]: https://github.com/diem/diem/tree/master/language/stdlib/transaction_scripts/doc "Move Stdlib scripts"
[5]: https://github.com/diem/diem/blob/master/client/diem-dev/README.md "Diem Client Dev Doc"
[6]: https://github.com/diem/diem/blob/master/json-rpc/docs/service_testnet_faucet.md "Faucet service"
[7]: https://github.com/diem/lip/blob/master/lips/lip-4.md "Transaction Metadata Specification"
