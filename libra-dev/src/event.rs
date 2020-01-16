// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

use crate::data::{LibraEvent, LibraEventType, LibraPaymentEvent, LibraStatus};
use libra_types::{
    account_address::ADDRESS_LENGTH, account_config::ReceivedPaymentEvent,
    account_config::SentPaymentEvent, contract_event::ContractEvent, event::EventKey,
    event::EVENT_KEY_LENGTH, language_storage::TypeTag,
};
use std::convert::TryFrom;
use std::ffi::CString;
use std::slice;

#[no_mangle]
pub unsafe extern "C" fn libra_LibraEvent_from(
    buf_key: *const u8,
    len_key: usize,
    buf_data: *const u8,
    len_data: usize,
    buf_type_tag: *const u8,
    len_type_tag: usize,
    out: *mut LibraEvent,
) -> LibraStatus {
    let buffer_key: &[u8] = slice::from_raw_parts(buf_key, len_key);
    let buffer_data: &[u8] = slice::from_raw_parts(buf_data, len_data);
    let buffer_type_tag: &[u8] = slice::from_raw_parts(buf_type_tag, len_type_tag);

    let mut key = [0u8; EVENT_KEY_LENGTH];
    key.copy_from_slice(buffer_key);

    let (_salt, event_address) = buffer_key.split_at(8);
    let mut key_address = [0u8; ADDRESS_LENGTH];
    key_address.copy_from_slice(event_address);

    let type_tag: TypeTag = match lcs::from_bytes(buffer_type_tag) {
        Ok(result) => result,
        Err(_e) => {
            return LibraStatus::InvalidArgument;
        }
    };

    let mut module = [0u8; 255];
    if let TypeTag::Struct(struct_tag) = type_tag.clone() {
        let module_tmp = match CString::new(struct_tag.module.into_string()) {
            Ok(res) => res,
            _ => return LibraStatus::InvalidArgument,
        };
        let module_bytes = module_tmp.as_bytes_with_nul();
        let module_len = module_bytes.len();
        module[..module_len].copy_from_slice(module_bytes);
    };

    let account_event = ContractEvent::new(EventKey::new(key), 0, type_tag, buffer_data.to_vec());

    let mut event_enum = None;
    let mut event_data: Option<LibraPaymentEvent> = None;

    match SentPaymentEvent::try_from(&account_event) {
        Ok(res) => {
            event_enum = Some(LibraEventType::SentPaymentEvent);
            let mut addr = [0u8; ADDRESS_LENGTH];
            addr.copy_from_slice(res.receiver().as_ref());
            event_data = Some(LibraPaymentEvent {
                sender_address: key_address,
                receiver_address: addr,
                amount: res.amount(),
                module,
            });
        }
        _ => {}
    };

    match ReceivedPaymentEvent::try_from(&account_event) {
        Ok(res) => {
            event_enum = Some(LibraEventType::ReceivedPaymentEvent);
            let mut addr = [0u8; ADDRESS_LENGTH];
            addr.copy_from_slice(res.sender().as_ref());
            event_data = Some(LibraPaymentEvent {
                sender_address: addr,
                receiver_address: key_address,
                amount: res.amount(),
                module,
            });
        }
        _ => {}
    };

    match event_enum {
        Some(_) => {}
        None => {
            return LibraStatus::InvalidArgument;
        }
    };

    match event_data {
        Some(_) => {}
        None => {
            return LibraStatus::InvalidArgument;
        }
    }

    *out = LibraEvent {
        event_type: event_enum.unwrap(),
        payment_event: event_data.unwrap(),
    };

    LibraStatus::OK
}

#[test]
fn test_libra_LibraEvent_from() {
    use libra_crypto::ed25519::compat;
    use libra_types::{
        account_address::AccountAddress,
        account_config::SentPaymentEvent,
        contract_event::ContractEvent,
        event::{EventHandle, EventKey},
        identifier::Identifier,
        language_storage::{StructTag, TypeTag::Struct},
    };
    use std::ffi::CStr;

    let keypair = compat::generate_keypair(None);
    let public_key = keypair.1;
    let sender_address = AccountAddress::from_public_key(&public_key);
    let sent_event_handle = EventHandle::new(EventKey::new_from_address(&sender_address, 0), 0);
    let sequence_number = sent_event_handle.count();
    let event_key = sent_event_handle.key();
    let module = "LibraAccount";

    let type_tag = Struct(StructTag {
        address: AccountAddress::new([0; 32]),
        module: Identifier::new(module).unwrap(),
        name: Identifier::new("SentPaymentEvent").unwrap(),
        type_params: [].to_vec(),
    });
    let amount = 50000000;
    let receiver_address = AccountAddress::random();
    let event_data = SentPaymentEvent::new(amount, receiver_address, vec![]);
    let event_data_bytes = lcs::to_bytes(&event_data).unwrap();

    let event = ContractEvent::new(*event_key, sequence_number, type_tag, event_data_bytes);

    let proto_txn = libra_types::proto::types::Event::from(event.clone());

    let mut libra_event = LibraEvent::default();
    let result = unsafe {
        libra_LibraEvent_from(
            proto_txn.key.as_ptr(),
            proto_txn.key.len(),
            proto_txn.event_data.as_ptr(),
            proto_txn.event_data.len(),
            proto_txn.type_tag.as_ptr(),
            proto_txn.type_tag.len(),
            &mut libra_event,
        )
    };
    assert_eq!(result, LibraStatus::OK);

    assert_eq!(
        sender_address,
        AccountAddress::new(libra_event.payment_event.sender_address)
    );
    assert_eq!(
        receiver_address,
        AccountAddress::new(libra_event.payment_event.receiver_address),
    );
    assert_eq!(amount, libra_event.payment_event.amount);

    let module_c_string: &CStr =
        unsafe { CStr::from_ptr(libra_event.payment_event.module.as_ptr() as *const i8) };
    let module_str_slice: &str = module_c_string.to_str().unwrap();

    assert_eq!(module_str_slice, module);
    assert_eq!(libra_event.event_type, LibraEventType::SentPaymentEvent);
}
