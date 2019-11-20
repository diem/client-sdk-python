// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

use lcs::to_bytes;
use libra_crypto::{ed25519::*, test_utils::KeyPair};
use libra_types::{
    account_address::{AccountAddress, ADDRESS_LENGTH},
    transaction::{helpers::TransactionSigner, RawTransaction, TransactionPayload},
};
use std::{convert::TryFrom, slice, time::Duration};
use transaction_builder::encode_transfer_script;

#[no_mangle]
pub extern "C" fn libra_signed_transaction_build(
    sender: *const u8,
    receiver: *const u8,
    sequence: u64,
    num_coins: u64,
    max_gas_amount: u64,
    gas_unit_price: u64,
    expiration_time_millis: u64,
    private_key_bytes: *const u8,
    buf: *mut *mut u8,
    len: *mut usize,
) {
    let sender_buf = unsafe { slice::from_raw_parts(sender, ADDRESS_LENGTH) };
    let sender_address = AccountAddress::try_from(sender_buf).unwrap();
    let receiver_buf = unsafe { slice::from_raw_parts(receiver, ADDRESS_LENGTH) };
    let receiver_address = AccountAddress::try_from(receiver_buf).unwrap();
    let expiration_time = Duration::from_millis(expiration_time_millis);

    let program = encode_transfer_script(&receiver_address, num_coins);
    let payload = TransactionPayload::Script(program);
    let raw_txn = RawTransaction::new(
        sender_address,
        sequence,
        payload,
        max_gas_amount,
        gas_unit_price,
        expiration_time,
    );

    let private_key_buf: &[u8] =
        unsafe { slice::from_raw_parts(private_key_bytes, ED25519_PRIVATE_KEY_LENGTH) };
    let private_key =
        Ed25519PrivateKey::try_from(private_key_buf).expect("Unable to deserialize Private Key");
    let key_pair = KeyPair::from(private_key);
    let signer: Box<&dyn TransactionSigner> = Box::new(&key_pair);

    let signed_txn = signer
        .sign_txn(raw_txn)
        .expect("Unable to sign transaction");

    let signed_txn_bytes = to_bytes(&signed_txn).expect("Unable to serialize SignedTransaction");
    unsafe {
        let txn_buf: (*mut u8) = libc::malloc(signed_txn_bytes.len()).cast();
        txn_buf.copy_from(signed_txn_bytes.as_ptr(), signed_txn_bytes.len());

        *buf = txn_buf;
        *len = signed_txn_bytes.len();
    }
}

#[no_mangle]
pub unsafe extern "C" fn libra_signed_transaction_free(buf: *mut *mut u8) {
    if !buf.is_null() {
        libc::free(*buf as *mut libc::c_void);
    }
}

/// Generate an Signed Transaction and deserialize
#[test]
fn test_lcs_signed_transaction() {
    use lcs::from_bytes;
    use libra_crypto::test_utils::TEST_SEED;
    use libra_types::transaction::{SignedTransaction, TransactionArgument};
    use rand::{rngs::StdRng, SeedableRng};

    // generate key pair
    let mut rng = StdRng::from_seed(TEST_SEED);
    let key_pair = compat::generate_keypair(&mut rng);
    let private_key = key_pair.0;
    let public_key = key_pair.1;
    let private_key_bytes = private_key.to_bytes();

    // create transfer parameters
    let sender_address = AccountAddress::from_public_key(&public_key);
    let receiver_address = AccountAddress::random();
    let sequence = 0;
    let amount = 100000000;
    let gas_unit_price = 123;
    let max_gas_amount = 1000;
    let expiration_time_millis = 0;

    let mut buf: u8 = 0;
    let mut buf_ptr: *mut u8 = &mut buf;
    let mut len: usize = 0;

    unsafe {
        libra_signed_transaction_build(
            sender_address.as_ref().as_ptr(),
            receiver_address.as_ref().as_ptr(),
            sequence,
            amount,
            max_gas_amount,
            gas_unit_price,
            expiration_time_millis,
            private_key_bytes.as_ptr(),
            &mut buf_ptr,
            &mut len,
        )
    };

    let signed_txn_bytes_buf: &[u8] = unsafe { slice::from_raw_parts(buf_ptr, len) };
    let deserialized_signed_txn: SignedTransaction =
        from_bytes(signed_txn_bytes_buf).expect("LCS deserialization failed");

    if let TransactionPayload::Script(program) = deserialized_signed_txn.payload() {
        if let TransactionArgument::U64(val) = program.args()[1] {
            assert_eq!(val, amount);
        }
    }
    assert_eq!(deserialized_signed_txn.sequence_number(), 0);
    assert_eq!(deserialized_signed_txn.gas_unit_price(), gas_unit_price);
    assert_eq!(deserialized_signed_txn.public_key(), public_key);
    assert!(deserialized_signed_txn.check_signature().is_ok());

    unsafe { libra_signed_transaction_free(&mut buf_ptr) };
}
