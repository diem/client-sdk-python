#ifndef LIBRA_DEV_H
#define LIBRA_DEV_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

struct CEventHandle {
    uint64_t count;
    uint8_t key[32];
};

struct CDevAccountResource {
    uint64_t balance;
    uint64_t sequence;
    uint8_t authentication_key[32];
    bool delegated_key_rotation_capability;
    bool delegated_withdrawal_capability;
    struct CEventHandle sent_events;
    struct CEventHandle received_events;
};

struct LibraP2PTransferTransactionArgument {
    uint64_t value;
    uint8_t address[32];
};

enum TransactionType {
    PeerToPeer = 0,
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

struct CDevAccountResource account_resource_from_lcs(const uint8_t *buf, size_t len);
void account_resource_free(struct CDevAccountResource *point);
/*!
 * To get the serialized transaction in a memory safe manner, the client needs to pass in a pointer to a pointer to the allocated memory in rust
 * and call free on the memory address with `libra_SignedTransactionBytes_free`.
 * @param[out] buf is the pointer that will be filled with the memory address of the transaction allocated in rust. User takes ownership of pointer returned by *buf, which needs to be freed using libra_signed_transcation_free
 * @param[out] len is the length of the signed transaction memory buffer.
*/
void libra_SignedTransactionBytes_from(const uint8_t sender[32], const uint8_t receiver[32], uint64_t sequence, uint64_t num_coins, uint64_t max_gas_amount, uint64_t gas_unit_price, uint64_t expiration_time_secs, const uint8_t* private_key_bytes, uint8_t** ptr_buf, size_t* ptr_len);
/*!
 * Function to free the allocation memory in rust for transaction
 * @param buf is the pointer to the transaction allocated in rust, and needs to be freed from client side
 */
void libra_SignedTransactionBytes_free(const uint8_t* buf);
struct LibraSignedTransaction libra_LibraSignedTransaction_from(const uint8_t *buf, size_t len);

#ifdef __cplusplus
};
#endif

#endif // LIBRA_DEV_H