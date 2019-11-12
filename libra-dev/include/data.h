#ifndef LIBRA_DEV_H
#define LIBRA_DEV_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>

struct CEventHandle {
    uint64_t count;
    uint8_t key[32];
};

struct CDevAccountResource {
    uint64_t balance;
    uint64_t sequence;
    uint8_t* authentication_key;
    bool delegated_key_rotation_capability;
    bool delegated_withdrawal_capability;
    struct CEventHandle sent_events;
    struct CEventHandle received_events;
};

struct CDevAccountResource account_resource_from_lcs(const uint8_t *buf, size_t len);
void account_resource_free(struct CDevAccountResource *point);


#ifdef __cplusplus
};
#endif

#endif // LIBRA_DEV_H