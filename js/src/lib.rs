use wasm_bindgen::prelude::*;

pub use libra_dev::account::*;

use serde::Deserialize;
use serde::Serialize;

#[derive(Copy, Clone, Serialize, Deserialize)]
struct AccountResource {
    pub balance: u64,
    pub sequence: u64,
    pub authentication_key: [u8; 32usize],
    pub delegated_key_rotation_capability: bool,
    pub delegated_withdrawal_capability: bool,
}

#[wasm_bindgen]
pub fn pubkey(private_key_hex: &str) -> String {
    let private_key = hex::decode(private_key_hex).expect("decode");

    hex::encode(
        libra_dev::account::LibraAccount_from(private_key.as_slice())
            .expect("test")
            .public_key,
    )
}

#[wasm_bindgen]
pub fn address(private_key_hex: &str) -> String {
    let private_key = hex::decode(private_key_hex).expect("decode");

    hex::encode(
        libra_dev::account::LibraAccount_from(private_key.as_slice())
            .expect("test")
            .address,
    )
}

#[wasm_bindgen]
pub fn account_state(blob_hex: &str) -> String {
    let ar = &libra_dev::account_resource::libra_LibraAccountResource_from_safe(
        hex::decode(blob_hex).expect("decode").into(),
    )
    .expect("test");

    serde_json::to_string(&AccountResource {
        balance: ar.balance,
        sequence: ar.sequence,
        authentication_key: ar.authentication_key,
        delegated_key_rotation_capability: ar.delegated_key_rotation_capability,
        delegated_withdrawal_capability: ar.delegated_withdrawal_capability,
    })
    .expect("test")
}
