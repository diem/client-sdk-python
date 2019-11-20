/* automatically generated by rust-bindgen */

#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct CEventHandle {
    pub count: u64,
    pub key: [u8; 32usize],
}
#[test]
fn bindgen_test_layout_CEventHandle() {
    assert_eq!(
        ::std::mem::size_of::<CEventHandle>(),
        40usize,
        concat!("Size of: ", stringify!(CEventHandle))
    );
    assert_eq!(
        ::std::mem::align_of::<CEventHandle>(),
        8usize,
        concat!("Alignment of ", stringify!(CEventHandle))
    );
    assert_eq!(
        unsafe { &(*(::std::ptr::null::<CEventHandle>())).count as *const _ as usize },
        0usize,
        concat!(
            "Offset of field: ",
            stringify!(CEventHandle),
            "::",
            stringify!(count)
        )
    );
    assert_eq!(
        unsafe { &(*(::std::ptr::null::<CEventHandle>())).key as *const _ as usize },
        8usize,
        concat!(
            "Offset of field: ",
            stringify!(CEventHandle),
            "::",
            stringify!(key)
        )
    );
}
#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct CDevAccountResource {
    pub balance: u64,
    pub sequence: u64,
    pub authentication_key: [u8; 32usize],
    pub delegated_key_rotation_capability: bool,
    pub delegated_withdrawal_capability: bool,
    pub sent_events: CEventHandle,
    pub received_events: CEventHandle,
}
#[test]
fn bindgen_test_layout_CDevAccountResource() {
    assert_eq!(
        ::std::mem::size_of::<CDevAccountResource>(),
        136usize,
        concat!("Size of: ", stringify!(CDevAccountResource))
    );
    assert_eq!(
        ::std::mem::align_of::<CDevAccountResource>(),
        8usize,
        concat!("Alignment of ", stringify!(CDevAccountResource))
    );
    assert_eq!(
        unsafe { &(*(::std::ptr::null::<CDevAccountResource>())).balance as *const _ as usize },
        0usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevAccountResource),
            "::",
            stringify!(balance)
        )
    );
    assert_eq!(
        unsafe { &(*(::std::ptr::null::<CDevAccountResource>())).sequence as *const _ as usize },
        8usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevAccountResource),
            "::",
            stringify!(sequence)
        )
    );
    assert_eq!(
        unsafe {
            &(*(::std::ptr::null::<CDevAccountResource>())).authentication_key as *const _ as usize
        },
        16usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevAccountResource),
            "::",
            stringify!(authentication_key)
        )
    );
    assert_eq!(
        unsafe {
            &(*(::std::ptr::null::<CDevAccountResource>())).delegated_key_rotation_capability
                as *const _ as usize
        },
        48usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevAccountResource),
            "::",
            stringify!(delegated_key_rotation_capability)
        )
    );
    assert_eq!(
        unsafe {
            &(*(::std::ptr::null::<CDevAccountResource>())).delegated_withdrawal_capability
                as *const _ as usize
        },
        49usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevAccountResource),
            "::",
            stringify!(delegated_withdrawal_capability)
        )
    );
    assert_eq!(
        unsafe { &(*(::std::ptr::null::<CDevAccountResource>())).sent_events as *const _ as usize },
        56usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevAccountResource),
            "::",
            stringify!(sent_events)
        )
    );
    assert_eq!(
        unsafe {
            &(*(::std::ptr::null::<CDevAccountResource>())).received_events as *const _ as usize
        },
        96usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevAccountResource),
            "::",
            stringify!(received_events)
        )
    );
}
#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct CDevP2PTransferTransactionArgument {
    pub value: u64,
    pub address: [u8; 32usize],
}
#[test]
fn bindgen_test_layout_CDevP2PTransferTransactionArgument() {
    assert_eq!(
        ::std::mem::size_of::<CDevP2PTransferTransactionArgument>(),
        40usize,
        concat!("Size of: ", stringify!(CDevP2PTransferTransactionArgument))
    );
    assert_eq!(
        ::std::mem::align_of::<CDevP2PTransferTransactionArgument>(),
        8usize,
        concat!(
            "Alignment of ",
            stringify!(CDevP2PTransferTransactionArgument)
        )
    );
    assert_eq!(
        unsafe {
            &(*(::std::ptr::null::<CDevP2PTransferTransactionArgument>())).value as *const _
                as usize
        },
        0usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevP2PTransferTransactionArgument),
            "::",
            stringify!(value)
        )
    );
    assert_eq!(
        unsafe {
            &(*(::std::ptr::null::<CDevP2PTransferTransactionArgument>())).address as *const _
                as usize
        },
        8usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevP2PTransferTransactionArgument),
            "::",
            stringify!(address)
        )
    );
}
pub const TransactionType_PeerToPeer: TransactionType = 0;
pub type TransactionType = u32;
#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct CDevTransactionPayload {
    pub txn_type: TransactionType,
    pub args: CDevP2PTransferTransactionArgument,
}
#[test]
fn bindgen_test_layout_CDevTransactionPayload() {
    assert_eq!(
        ::std::mem::size_of::<CDevTransactionPayload>(),
        48usize,
        concat!("Size of: ", stringify!(CDevTransactionPayload))
    );
    assert_eq!(
        ::std::mem::align_of::<CDevTransactionPayload>(),
        8usize,
        concat!("Alignment of ", stringify!(CDevTransactionPayload))
    );
    assert_eq!(
        unsafe { &(*(::std::ptr::null::<CDevTransactionPayload>())).txn_type as *const _ as usize },
        0usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevTransactionPayload),
            "::",
            stringify!(txn_type)
        )
    );
    assert_eq!(
        unsafe { &(*(::std::ptr::null::<CDevTransactionPayload>())).args as *const _ as usize },
        8usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevTransactionPayload),
            "::",
            stringify!(args)
        )
    );
}
#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct CDevRawTransaction {
    pub sender: [u8; 32usize],
    pub sequence_number: u64,
    pub payload: CDevTransactionPayload,
    pub max_gas_amount: u64,
    pub gas_unit_price: u64,
    pub expiration_time_secs: u64,
}
#[test]
fn bindgen_test_layout_CDevRawTransaction() {
    assert_eq!(
        ::std::mem::size_of::<CDevRawTransaction>(),
        112usize,
        concat!("Size of: ", stringify!(CDevRawTransaction))
    );
    assert_eq!(
        ::std::mem::align_of::<CDevRawTransaction>(),
        8usize,
        concat!("Alignment of ", stringify!(CDevRawTransaction))
    );
    assert_eq!(
        unsafe { &(*(::std::ptr::null::<CDevRawTransaction>())).sender as *const _ as usize },
        0usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevRawTransaction),
            "::",
            stringify!(sender)
        )
    );
    assert_eq!(
        unsafe {
            &(*(::std::ptr::null::<CDevRawTransaction>())).sequence_number as *const _ as usize
        },
        32usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevRawTransaction),
            "::",
            stringify!(sequence_number)
        )
    );
    assert_eq!(
        unsafe { &(*(::std::ptr::null::<CDevRawTransaction>())).payload as *const _ as usize },
        40usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevRawTransaction),
            "::",
            stringify!(payload)
        )
    );
    assert_eq!(
        unsafe {
            &(*(::std::ptr::null::<CDevRawTransaction>())).max_gas_amount as *const _ as usize
        },
        88usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevRawTransaction),
            "::",
            stringify!(max_gas_amount)
        )
    );
    assert_eq!(
        unsafe {
            &(*(::std::ptr::null::<CDevRawTransaction>())).gas_unit_price as *const _ as usize
        },
        96usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevRawTransaction),
            "::",
            stringify!(gas_unit_price)
        )
    );
    assert_eq!(
        unsafe {
            &(*(::std::ptr::null::<CDevRawTransaction>())).expiration_time_secs as *const _ as usize
        },
        104usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevRawTransaction),
            "::",
            stringify!(expiration_time_secs)
        )
    );
}
#[repr(C)]
#[derive(Copy, Clone)]
pub struct CDevSignedTransaction {
    pub raw_txn: CDevRawTransaction,
    pub public_key: [u8; 32usize],
    pub signature: [u8; 64usize],
}
#[test]
fn bindgen_test_layout_CDevSignedTransaction() {
    assert_eq!(
        ::std::mem::size_of::<CDevSignedTransaction>(),
        208usize,
        concat!("Size of: ", stringify!(CDevSignedTransaction))
    );
    assert_eq!(
        ::std::mem::align_of::<CDevSignedTransaction>(),
        8usize,
        concat!("Alignment of ", stringify!(CDevSignedTransaction))
    );
    assert_eq!(
        unsafe { &(*(::std::ptr::null::<CDevSignedTransaction>())).raw_txn as *const _ as usize },
        0usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevSignedTransaction),
            "::",
            stringify!(raw_txn)
        )
    );
    assert_eq!(
        unsafe {
            &(*(::std::ptr::null::<CDevSignedTransaction>())).public_key as *const _ as usize
        },
        112usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevSignedTransaction),
            "::",
            stringify!(public_key)
        )
    );
    assert_eq!(
        unsafe { &(*(::std::ptr::null::<CDevSignedTransaction>())).signature as *const _ as usize },
        144usize,
        concat!(
            "Offset of field: ",
            stringify!(CDevSignedTransaction),
            "::",
            stringify!(signature)
        )
    );
}
