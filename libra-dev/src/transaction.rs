// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

use crate::data::{
    LibraP2PTransferTransactionArgument, LibraRawTransaction, LibraSignedTransaction, LibraStatus,
    LibraTransactionPayload, TransactionType,
};
use lcs::to_bytes;
use libra_crypto::{ed25519::*, test_utils::KeyPair};
use libra_types::transaction::SignedTransaction;
use libra_types::{
    account_address::{AccountAddress, ADDRESS_LENGTH},
    transaction::{
        helpers::TransactionSigner, RawTransaction, TransactionArgument, TransactionPayload,
    },
};
use std::{convert::TryFrom, slice, time::Duration};
use transaction_builder::encode_transfer_script;

#[no_mangle]
pub unsafe extern "C" fn libra_SignedTransactionBytes_from(
    sender: *const u8,
    receiver: *const u8,
    sequence: u64,
    num_coins: u64,
    max_gas_amount: u64,
    gas_unit_price: u64,
    expiration_time_secs: u64,
    private_key_bytes: *const u8,
    ptr_buf: *mut *mut u8,
    ptr_len: *mut usize,
) -> LibraStatus {
    let sender_buf = slice::from_raw_parts(sender, ADDRESS_LENGTH);
    let sender_address = match AccountAddress::try_from(sender_buf) {
        Ok(result) => result,
        Err(_e) => {
            return LibraStatus::InvalidArgument;
        }
    };

    let receiver_buf = slice::from_raw_parts(receiver, ADDRESS_LENGTH);
    let receiver_address = match AccountAddress::try_from(receiver_buf) {
        Ok(result) => result,
        Err(_e) => {
            return LibraStatus::InvalidArgument;
        }
    };

    let expiration_time = Duration::from_secs(expiration_time_secs);

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
        slice::from_raw_parts(private_key_bytes, ED25519_PRIVATE_KEY_LENGTH);
    let private_key = match Ed25519PrivateKey::try_from(private_key_buf) {
        Ok(result) => result,
        Err(_e) => {
            return LibraStatus::InvalidArgument;
        }
    };

    let key_pair = KeyPair::from(private_key);
    let signer: Box<&dyn TransactionSigner> = Box::new(&key_pair);
    let signed_txn = match signer.sign_txn(raw_txn) {
        Ok(result) => result,
        Err(_e) => {
            return LibraStatus::InvalidArgument;
        }
    };

    let signed_txn_bytes = match to_bytes(&signed_txn) {
        Ok(result) => result,
        Err(_e) => {
            return LibraStatus::InternalError;
        }
    };
    let txn_buf: (*mut u8) = libc::malloc(signed_txn_bytes.len()).cast();
    txn_buf.copy_from(signed_txn_bytes.as_ptr(), signed_txn_bytes.len());

    *ptr_buf = txn_buf;
    *ptr_len = signed_txn_bytes.len();

    LibraStatus::OK
}

#[no_mangle]
pub unsafe extern "C" fn libra_SignedTransactionBytes_free(buf: *const u8) {
    if !buf.is_null() {
        libc::free(buf as *mut libc::c_void);
    }
}

#[no_mangle]
pub unsafe extern "C" fn libra_LibraSignedTransaction_from(
    buf: *const u8,
    len: usize,
    out: *mut LibraSignedTransaction,
) -> LibraStatus {
    if buf.is_null() {
        return LibraStatus::InvalidArgument;
    }
    let buffer: &[u8] = slice::from_raw_parts(buf, len);
    let signed_txn: SignedTransaction = match lcs::from_bytes(&buffer) {
        Ok(result) => result,
        Err(_e) => {
            return LibraStatus::InvalidArgument;
        }
    };

    let mut sender = [0u8; ADDRESS_LENGTH];
    sender.copy_from_slice(signed_txn.sender().as_ref());
    let sequence_number = signed_txn.sequence_number();
    let payload = signed_txn.payload();
    let max_gas_amount = signed_txn.max_gas_amount();
    let gas_unit_price = signed_txn.gas_unit_price();
    let expiration_time_secs = signed_txn.expiration_time().as_secs();
    let public_key = signed_txn.public_key();
    let signature = signed_txn.signature();

    let mut txn_payload = None;

    if let TransactionPayload::Script(script) = payload {
        let args = script.args();
        let mut value = None;
        let mut address = None;
        args.iter().for_each(|txn_arg| match txn_arg {
            TransactionArgument::U64(val) => {
                value = Some(*val);
            }
            TransactionArgument::Address(addr) => {
                let mut addr_buffer = [0u8; ADDRESS_LENGTH];
                addr_buffer.copy_from_slice(addr.as_ref());
                address = Some(addr_buffer);
            }
            _ => {}
        });
        if let (Some(val), Some(add)) = (value, address) {
            txn_payload = Some(LibraTransactionPayload {
                txn_type: TransactionType::PeerToPeer,
                args: LibraP2PTransferTransactionArgument {
                    value: val,
                    address: add,
                },
            });
        };
    }

    let payload = match txn_payload {
        Some(val) => val,
        None => {
            return LibraStatus::InvalidArgument;
        }
    };

    let raw_txn = LibraRawTransaction {
        sender,
        sequence_number,
        payload,
        max_gas_amount,
        gas_unit_price,
        expiration_time_secs,
    };
    *out = LibraSignedTransaction {
        raw_txn,
        public_key: public_key.to_bytes(),
        signature: signature.to_bytes(),
    };

    LibraStatus::OK
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
    let expiration_time_secs = 0;

    let mut buf: u8 = 0;
    let mut buf_ptr: *mut u8 = &mut buf;
    let mut len: usize = 0;

    let result = unsafe {
        libra_SignedTransactionBytes_from(
            sender_address.as_ref().as_ptr(),
            receiver_address.as_ref().as_ptr(),
            sequence,
            amount,
            max_gas_amount,
            gas_unit_price,
            expiration_time_secs,
            private_key_bytes.as_ptr(),
            &mut buf_ptr,
            &mut len,
        )
    };

    assert_eq!(result, LibraStatus::OK);

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

    unsafe { libra_SignedTransactionBytes_free(buf_ptr) };
}

/// Generate an Signed Transaction and deserialize
#[test]
fn test_libra_signed_transaction_deserialize() {
    let keypair = compat::generate_keypair(None);
    let sender = AccountAddress::random();
    let receiver = AccountAddress::random();
    let sequence_number = 1;
    let amount = 10000000;
    let max_gas_amount = 10;
    let gas_unit_price = 1;
    let expiration_time_secs = 5;
    let public_key = keypair.1;
    let signature = Ed25519Signature::try_from(&[1u8; 64][..]).unwrap();

    let program = encode_transfer_script(&receiver, amount);
    let signed_txn = SignedTransaction::new(
        RawTransaction::new_script(
            sender,
            sequence_number,
            program,
            max_gas_amount,
            gas_unit_price,
            Duration::from_secs(expiration_time_secs),
        ),
        public_key.clone(),
        signature.clone(),
    );
    let proto_txn: libra_types::proto::types::SignedTransaction = signed_txn.clone().into();

    let mut libra_signed_txn = LibraSignedTransaction::default();
    let result = unsafe {
        libra_LibraSignedTransaction_from(
            proto_txn.txn_bytes.as_ptr(),
            proto_txn.txn_bytes.len() - 1, // pass in wrong length so that SignedTransaction cannot deserialize
            &mut libra_signed_txn,
        )
    };
    assert_eq!(result, LibraStatus::InvalidArgument);

    let result = unsafe {
        libra_LibraSignedTransaction_from(
            proto_txn.txn_bytes.as_ptr(),
            proto_txn.txn_bytes.len(),
            &mut libra_signed_txn,
        )
    };
    assert_eq!(result, LibraStatus::OK);

    let payload = signed_txn.payload();
    if let TransactionPayload::Script(_script) = payload {
        assert_eq!(
            TransactionType::PeerToPeer,
            libra_signed_txn.raw_txn.payload.txn_type
        );
        assert_eq!(
            receiver,
            AccountAddress::new(libra_signed_txn.raw_txn.payload.args.address)
        );
        assert_eq!(amount, libra_signed_txn.raw_txn.payload.args.value);
    }
    assert_eq!(sender, AccountAddress::new(libra_signed_txn.raw_txn.sender));
    assert_eq!(sequence_number, libra_signed_txn.raw_txn.sequence_number);
    assert_eq!(max_gas_amount, libra_signed_txn.raw_txn.max_gas_amount);
    assert_eq!(gas_unit_price, libra_signed_txn.raw_txn.gas_unit_price);
    assert_eq!(public_key.to_bytes(), libra_signed_txn.public_key);
    assert_eq!(
        signature,
        Ed25519Signature::try_from(libra_signed_txn.signature.as_ref()).unwrap()
    );
    assert_eq!(
        expiration_time_secs,
        libra_signed_txn.raw_txn.expiration_time_secs
    );
}
