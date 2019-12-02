#ifndef LIBRA_DEV_H
#define LIBRA_DEV_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

const char* LIBRA_VERSION = "3160002c771bbf325d71759a0192ae567d586f22";

enum LibraStatus {
    OK = 0,
    InvalidArgument = -1,
    InternalError = -255,
};

struct LibraEventHandle {
    uint64_t count;
    uint8_t key[40];
};

struct LibraAccountResource {
    uint64_t balance;
    uint64_t sequence;
    uint8_t authentication_key[32];
    bool delegated_key_rotation_capability;
    bool delegated_withdrawal_capability;
    struct LibraEventHandle sent_events;
    struct LibraEventHandle received_events;
};

struct LibraP2PTransferTransactionArgument {
    uint64_t value;
    uint8_t address[32];
};

enum TransactionType {
    PeerToPeer = 0,
    Mint = 1,
    Unknown = -1,
};

struct LibraTransactionPayload {
    enum TransactionType txn_type;
    struct LibraP2PTransferTransactionArgument args; //
};

struct LibraRawTransaction {
    uint8_t sender[32];
    uint64_t sequence_number;
    struct LibraTransactionPayload payload;
    uint64_t max_gas_amount;
    uint64_t gas_unit_price;
    uint64_t expiration_time_secs;
};

struct LibraSignedTransaction {
    struct LibraRawTransaction raw_txn;
    uint8_t public_key[32];
    uint8_t signature[64];
};

struct LibraAccountKey {
    uint8_t address[32];
    uint8_t private_key[32];
    uint8_t public_key[32];
};

enum LibraEventType {
    SentPaymentEvent = 1,
    ReceivedPaymentEvent = 2,
    UndefinedEvent = -1,
};

struct LibraPaymentEvent {
    uint8_t sender_address[32];
    uint8_t receiver_address[32];
    uint64_t amount;
    uint8_t* metadata;
    size_t metadata_len;
};

struct LibraEvent {
    enum LibraEventType event_type;
    // TODO: address
    uint8_t module[255];
    uint8_t name[255];
    // TODO: type_params
    struct LibraPaymentEvent payment_event_data;
    // TODO: other type of event_data
};

/*!
 * Decode LibraAccountResource from bytes in AccountStateBlob.
 *
 * @param[in] buf contains encoded bytes of AccountStateBlob
 * @param[in] len is the length of the signed AccountStateBlob memory buffer.
 * @param[out] caller allocated LibraAccountResource to write into.
 *
 * @returns status code, one of LibraAPIStatus
*/
enum LibraStatus libra_LibraAccountResource_from(const uint8_t *buf, size_t len, struct LibraAccountResource *out);

/*!
 *  Get serialized signed transaction from a list of transaction parameters
 *
 * To get the serialized transaction in a memory safe manner, the client needs to pass in a pointer to a pointer to the allocated memory in rust
 * and call free on the memory address with `libra_free_bytes_buffer`.
 * @param[in] expiration_time_secs is the time this TX remain valid, the format is unix timestamp.
 * @param[out] buf is the pointer that will be filled with the memory address of the transaction allocated in rust. User takes ownership of pointer returned by *buf, which needs to be freed using libra_signed_transcation_free
 * @param[out] len is the length of the signed transaction memory buffer.
*/
enum LibraStatus libra_SignedTransactionBytes_from(const uint8_t sender_private_key[32], const uint8_t receiver[32], uint64_t sequence, uint64_t num_coins, uint64_t max_gas_amount, uint64_t gas_unit_price, uint64_t expiration_time_secs, uint8_t** ptr_buf, size_t* ptr_len);

/*!
 * Function to free the allocation memory in rust for bytes
 * @param buf is the pointer to the bytes allocated in rust, and needs to be freed from client side
 */
void libra_free_bytes_buffer(const uint8_t* buf);

/*!
 * Decode LibraSignedTransaction from bytes in SignedTransaction proto.
 *
 * @param[in] buf contains encoded bytes of txn_bytes
 * @param[in] len is the length of the signed transaction memory buffer.
 * @param[out] caller allocated LibraSignedTransaction to write into.
 *
 * @returns status code, one of LibraAPIStatus
*/
enum LibraStatus libra_LibraSignedTransaction_from(const uint8_t *buf, size_t len, struct LibraSignedTransaction *out);

/*!
 * Get serialized raw transaction from a list of transaction parameters
 *
 * To get the serialized raw transaction in a memory safe manner, the client needs to pass in a pointer to a pointer to the allocated memory in rust
 * and call free on the memory address with `libra_free_bytes_buffer`.
 * @param[out] buf is the pointer that will be filled with the memory address of the transaction allocated in rust. User takes ownership of pointer returned by *buf, which needs to be freed using libra_free_bytes_buffer
 * @param[out] len is the length of the raw transaction memory buffer.
*/
enum LibraStatus libra_RawTransactionBytes_from(const uint8_t sender[32], const uint8_t receiver[32], uint64_t sequence, uint64_t num_coins, uint64_t max_gas_amount, uint64_t gas_unit_price, uint64_t expiration_time_secs, uint8_t** buf, size_t* len);

/*!
 * This function takes in a raw transaction, public key and signature in bytes, and return a signed transaction in bytes.
 * To get the serialized signed transaction in a memory safe manner, the client needs to pass in a pointer to a pointer to the allocated memory in rust
 * and call free on the memory address with `libra_free_bytes_buffer`.
 * @param[out] buf_result is the pointer that will be filled with the memory address of the transaction allocated in rust. User takes ownership of pointer returned by *buf, which needs to be freed using libra_free_bytes_buffer
 * @param[out] len_result is the length of the signed transaction memory buffer.
*/
enum LibraStatus libra_RawTransaction_sign(const uint8_t *buf_raw_txn, size_t len_raw_txn, const uint8_t *buf_public_key, size_t len_public_key, const uint8_t *buf_signature, size_t len_signature, uint8_t** buf_result, size_t* len_result);

enum LibraStatus libra_LibraAccount_from(const uint8_t private_key_bytes[32], struct LibraAccountKey *out);

/*!
 * This function takes in an event key, event data and event type tag in bytes, and return LibraEvent.
 * To get the event in a memory safe manner, the client needs to call free on the output with `libra_LibraEvent_free`.
 * @param[out] caller allocated LibraEvent to write into.
 * @returns status code, one of LibraStatus
*/
enum LibraStatus libra_LibraEvent_from(const uint8_t *buf_key, size_t len_key, const uint8_t *buf_data, size_t len_data, const uint8_t *buf_type_tag, size_t len_type_tag, struct LibraEvent **out);
void libra_LibraEvent_free(struct LibraEvent *out);

/*!
 * This function returns the string message of the most recent error in Rust.
 * If the allocated buffer is too short, it will return -1.
 * If the buffer is void, it will return -1.
 * On success, buffer will be filled with the string message of the last error.
 *
 * @param[out] caller allocated string buffer to write the error message to
 * @param[in] length of the buffer
 * @param[out] length of the returned error message
 * @returns int value indicating success or failure
*/
int32_t libra_strerror(char *buffer, int32_t* length);

#ifdef __cplusplus
};
#endif

#endif // LIBRA_DEV_H
