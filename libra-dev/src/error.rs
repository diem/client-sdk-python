// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

use once_cell::sync::Lazy;
use std::borrow::{Borrow, BorrowMut};
use std::cmp::min;
use std::os::raw::c_char;

const MAX_ERROR_LENGTH: usize = 1024;

static mut LAST_ERROR: Lazy<[u8; MAX_ERROR_LENGTH]> = Lazy::new(|| {
    return [0u8; MAX_ERROR_LENGTH];
});

/// Update the most recent error.
pub fn update_last_error(err: String) {
    let last_error: &mut [u8; 1024] = unsafe { &mut LAST_ERROR.borrow_mut() };
    let slice_str = err.into_bytes().into_boxed_slice();
    let min_error_length = min(slice_str.len(), MAX_ERROR_LENGTH - 1);
    last_error[..min_error_length].copy_from_slice(&slice_str[..min_error_length]);
    // null terminate the string
    last_error[min_error_length] = 0;
}

pub fn clear_error() {
    let last_error: &mut [u8; 1024] = unsafe { &mut LAST_ERROR.borrow_mut() };
    last_error[0] = 0;
}

#[no_mangle]
pub unsafe extern "C" fn libra_strerror() -> *const c_char {
    LAST_ERROR.borrow().as_ptr().cast()
}
