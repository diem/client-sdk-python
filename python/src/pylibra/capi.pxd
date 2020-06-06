#cython: language_level=3

from libc.stdint cimport *
from libc.stddef cimport *

DEF LIBRA_PUBKEY_SIZE = 32
DEF LIBRA_PRIVKEY_SIZE =  32
DEF LIBRA_ADDRESS_SIZE = 16
DEF LIBRA_EVENT_KEY_SIZE = 24

cdef enum LIBRA_CONST:
    _LIBRA_PUBKEY_SIZE = LIBRA_PUBKEY_SIZE
    _LIBRA_PRIVKEY_SIZE = LIBRA_PRIVKEY_SIZE
    _LIBRA_ADDRESS_SIZE = LIBRA_ADDRESS_SIZE
    _LIBRA_EVENT_KEY_SIZE = LIBRA_EVENT_KEY_SIZE

cdef extern from "data.h":
    enum LibraStatus:
        Ok = 0
        InvalidArgument = -1
        InternalError = -255

    struct LibraEventHandle:
        uint64_t count
        uint8_t[LIBRA_EVENT_KEY_SIZE] key

    struct LibraAccountResource:
        uint64_t balance
        uint64_t sequence
        uint8_t[LIBRA_PUBKEY_SIZE] authentication_key
        bint delegated_key_rotation_capability
        bint delegated_withdrawal_capability
        LibraEventHandle sent_events
        LibraEventHandle received_events


    struct LibraP2PTransferTransactionArgument:
        uint64_t value
        uint8_t[LIBRA_ADDRESS_SIZE] address
        uint8_t [LIBRA_PUBKEY_SIZE - LIBRA_ADDRESS_SIZE] auth_key_prefix
        uint8_t* metadata_bytes
        size_t metadata_len

    enum TransactionType:
        PeerToPeer = 0
        Mint = 1
        Unknown = -1

    struct LibraTransactionPayload:
        TransactionType txn_type
        LibraP2PTransferTransactionArgument args

    struct LibraRawTransaction:
        uint8_t[LIBRA_ADDRESS_SIZE] sender
        uint64_t sequence_number
        LibraTransactionPayload payload
        uint64_t max_gas_amount
        uint64_t gas_unit_price
        uint64_t expiration_time_secs

    struct LibraSignedTransaction:
        LibraRawTransaction raw_txn
        uint8_t[LIBRA_ADDRESS_SIZE] public_key
        uint8_t[64] signature

    struct LibraAccountKey:
        uint8_t[LIBRA_ADDRESS_SIZE] address
        uint8_t[LIBRA_PRIVKEY_SIZE] private_key
        uint8_t[LIBRA_PUBKEY_SIZE] public_key

    enum LibraEventType:
        SentPaymentEvent = 1
        ReceivedPaymentEvent = 2
        UndefinedEvent = -1

    struct LibraPaymentEvent:
        uint8_t[LIBRA_ADDRESS_SIZE] sender_address
        uint8_t[LIBRA_ADDRESS_SIZE] receiver_address
        uint64_t amount
        uint8_t* metadata
        size_t metadata_len

    struct LibraEvent:
        LibraEventType event_type
        uint8_t[255] module
        uint8_t[255] name
        LibraPaymentEvent payment_event_data


    LibraStatus libra_LibraAccountResource_from(const uint8_t *, size_t length, LibraAccountResource* out)
    LibraStatus libra_SignedTransactionBytes_from(const uint8_t sender_private_key[LIBRA_PRIVKEY_SIZE], uint64_t sequence, uint64_t max_gas_amount, uint64_t gas_unit_price, const char* gas_identifier, uint64_t expiration_time_secs, const uint8_t *script_bytes, size_t script_len, uint8_t **ptr_buf, size_t *ptr_len);
    LibraStatus libra_TransactionP2PScript_from(const uint8_t receiver[LIBRA_PUBKEY_SIZE], const char* identifier, uint64_t num_coins, const uint8_t* metadata_bytes, size_t metadata_len, const uint8_t* metadata_signature_bytes, size_t metadata_signature_len, uint8_t **ptr_buf, size_t *ptr_len);
    LibraStatus libra_TransactionAddCurrencyScript_from(const char* identifier, uint8_t **ptr_buf, size_t *ptr_len);
    void libra_free_bytes_buffer(const uint8_t* buf)
    LibraStatus libra_LibraSignedTransaction_from(const uint8_t *buf, size_t len, LibraSignedTransaction *out)
    LibraStatus libra_RawTransactionBytes_from(const uint8_t sender[LIBRA_ADDRESS_SIZE], const uint8_t receiver[LIBRA_PUBKEY_SIZE], uint64_t sequence, uint64_t num_coins, uint64_t max_gas_amount, uint64_t gas_unit_price, uint64_t expiration_time_secs, const uint8_t * metadata_bytes, size_t metadata_len, uint8_t** buf, size_t* len)
    LibraStatus libra_RawTransaction_sign(const uint8_t *buf_raw_txn, size_t len_raw_txn, const uint8_t *buf_public_key, size_t len_public_key, const uint8_t *buf_signature, size_t len_signature, uint8_t** buf_result, size_t* len_result)
    LibraStatus libra_LibraAccountKey_from(const uint8_t private_key_bytes[LIBRA_PRIVKEY_SIZE], LibraAccountKey *out)
    LibraStatus libra_LibraEvent_from(const uint8_t *buf_key, size_t len_key, const uint8_t *buf_data, size_t len_data, const uint8_t *buf_type_tag, size_t len_type_tag, LibraEvent** out)
    void libra_LibraEvent_free(LibraEvent* ptr)

