#cython: language_level=3

from libc.stdint cimport *
from libc.stddef cimport *

cdef extern from "data.h":
    enum LibraStatus:
        Ok = 0
        InvalidArgument = -1
        InternalError = -255

    struct LibraEventHandle:
        uint64_t count
        uint8_t[40] key

    struct LibraAccountResource:
        uint64_t balance
        uint64_t sequence
        uint8_t[32] authentication_key
        bint delegated_key_rotation_capability
        bint delegated_withdrawal_capability
        LibraEventHandle sent_events
        LibraEventHandle received_events


    struct LibraP2PTransferTransactionArgument:
        uint64_t value
        uint8_t[32] address

    enum TransactionType:
        PeerToPeer = 0
        Mint = 1
        Unknown = -1

    struct LibraTransactionPayload:
        TransactionType txn_type
        LibraP2PTransferTransactionArgument args

    struct LibraRawTransaction:
        uint8_t[32] sender
        uint64_t sequence_number
        LibraTransactionPayload payload
        uint64_t max_gas_amount
        uint64_t gas_unit_price
        uint64_t expiration_time_secs

    struct LibraSignedTransaction:
        LibraRawTransaction raw_txn
        uint8_t[32] public_key
        uint8_t[64] signature

    struct LibraAccountKey:
        uint8_t[32] address
        uint8_t[32] private_key
        uint8_t[32] public_key

    enum LibraEventType:
        SentPaymentEvent = 1
        ReceivedPaymentEvent = 2
        UndefinedEvent = -1

    struct LibraPaymentEvent:
        uint8_t[32] sender_address
        uint8_t[32] receiver_address
        uint64_t amount
        uint8_t* metadata
        size_t metadata_len

    struct LibraEvent:
        LibraEventType event_type
        uint8_t[255] module
        uint8_t[255] name
        LibraPaymentEvent payment_event_data


    LibraStatus libra_LibraAccountResource_from(const uint8_t *, size_t length, LibraAccountResource* out)
    LibraStatus libra_SignedTransactionBytes_from(const uint8_t sender_private_bytes[32], const uint8_t receiver[32], uint64_t sequence, uint64_t num_coins, uint64_t max_gas_amount, uint64_t gas_unit_price, uint64_t expiration_time_secs, uint8_t** ptr_buf, size_t* ptr_len)
    void libra_free_bytes_buffer(const uint8_t* buf)
    LibraStatus libra_LibraSignedTransaction_from(const uint8_t *buf, size_t len, LibraSignedTransaction *out)
    LibraStatus libra_RawTransactionBytes_from(const uint8_t sender[32], const uint8_t receiver[32], uint64_t sequence, uint64_t num_coins, uint64_t max_gas_amount, uint64_t gas_unit_price, uint64_t expiration_time_secs, uint8_t** buf, size_t* len)
    LibraStatus libra_RawTransaction_sign(const uint8_t *buf_raw_txn, size_t len_raw_txn, const uint8_t *buf_public_key, size_t len_public_key, const uint8_t *buf_signature, size_t len_signature, uint8_t** buf_result, size_t* len_result)
    LibraStatus libra_LibraAccountKey_from(const uint8_t private_key_bytes[32], LibraAccountKey *out)
    LibraStatus libra_LibraEvent_from(const uint8_t *buf_key, size_t len_key, const uint8_t *buf_data, size_t len_data, const uint8_t *buf_type_tag, size_t len_type_tag, LibraEvent** out)
    void libra_LibraEvent_free(LibraEvent* ptr)

