// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0
use crate::data::{CDevAccountResource, CEventHandle};
use libra_types::{
    account_config::get_account_resource_or_default, account_state_blob::AccountStateBlob,
    event::EVENT_KEY_LENGTH,
};
use std::slice;

#[no_mangle]
pub unsafe extern "C" fn account_resource_from_lcs(
    buf: *const u8,
    len: usize,
) -> CDevAccountResource {
    let buf: &[u8] = slice::from_raw_parts(buf, len);

    let account_state_blob = AccountStateBlob::from(buf.to_vec());
    let account_resource =
        get_account_resource_or_default(&Some(account_state_blob)).expect("fixme!");

    let mut authentication_key = [0u8; 32];
    authentication_key.copy_from_slice(account_resource.authentication_key().as_bytes());

    let mut sent_key_copy = [0u8; EVENT_KEY_LENGTH];
    sent_key_copy.copy_from_slice(account_resource.sent_events().key().as_bytes());

    let sent_events = CEventHandle {
        count: account_resource.sent_events().count(),
        key: sent_key_copy,
    };

    let mut received_key_copy = [0u8; EVENT_KEY_LENGTH];
    received_key_copy.copy_from_slice(account_resource.received_events().key().as_bytes());

    let received_events = CEventHandle {
        count: account_resource.received_events().count(),
        key: received_key_copy,
    };

    let result = CDevAccountResource {
        balance: account_resource.balance(),
        sequence: account_resource.sequence_number(),
        delegated_key_rotation_capability: account_resource.delegated_key_rotation_capability(),
        delegated_withdrawal_capability: account_resource.delegated_withdrawal_capability(),
        sent_events,
        received_events,
        authentication_key,
    };

    return result;
}

/// Generate an AccountBlob and verify we can parse it
#[test]
fn test_get_account_resource() {
    use libra_crypto::ed25519::compat;
    use libra_types::{
        account_address::AccountAddress, account_config::account_resource_path,
        account_config::AccountResource, byte_array::ByteArray, event::EventHandle,
    };
    use std::collections::BTreeMap;

    let keypair = compat::generate_keypair(None);

    // Figure out how to use Libra code to generate AccountStateBlob directly, not involving btreemap directly
    let mut map: BTreeMap<Vec<u8>, Vec<u8>> = BTreeMap::new();
    let ar = AccountResource::new(
        987654321,
        123456789,
        ByteArray::new(AccountAddress::from_public_key(&keypair.1).to_vec()),
        true,
        false,
        EventHandle::default(),
        EventHandle::default(),
    );

    // Fill in data
    map.insert(
        account_resource_path(),
        lcs::to_bytes(&ar).expect("Must success"),
    );

    let account_state_blob = lcs::to_bytes(&map).expect("LCS serialization failed");

    let result =
        unsafe { account_resource_from_lcs(account_state_blob.as_ptr(), account_state_blob.len()) };

    assert_eq!(result.balance, ar.balance());
    assert_eq!(result.sequence, ar.sequence_number());
    assert_eq!(
        result.authentication_key,
        ar.authentication_key().as_bytes()
    );
    assert_eq!(
        result.delegated_key_rotation_capability,
        ar.delegated_key_rotation_capability()
    );
    assert_eq!(
        result.delegated_withdrawal_capability,
        ar.delegated_withdrawal_capability()
    );
    assert_eq!(result.sent_events.count, ar.sent_events().count());
    assert_eq!(result.sent_events.key, ar.sent_events().key().as_bytes());
    assert_eq!(result.received_events.count, ar.received_events().count());
    assert_eq!(
        result.received_events.key,
        ar.received_events().key().as_bytes()
    );
}
