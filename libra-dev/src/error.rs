// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

use std::cell::RefCell;
use std::os::raw::{c_char, c_int};
use std::ptr;
use std::slice;

thread_local! {
    static LAST_ERROR: RefCell<Option<String>> = RefCell::new(None);
}

/// Update the most recent error, clearing whatever may have been there before.
pub fn update_last_error(err: String) {
    LAST_ERROR.with(|prev| {
        *prev.borrow_mut() = Some(err);
    });
}

/// Retrieve the most recent error, clearing it in the process.
pub fn take_last_error() -> Option<String> {
    LAST_ERROR.with(|prev| prev.borrow_mut().take())
}

#[no_mangle]
pub extern "C" fn last_error_length() -> c_int {
    LAST_ERROR.with(|prev| match *prev.borrow() {
        Some(ref err) => err.len() as c_int + 1,
        None => 0,
    })
}

#[no_mangle]
pub unsafe extern "C" fn libra_strerror(buffer: *mut c_char, length: *mut c_int) -> c_int {
    let last_error = match take_last_error() {
        Some(err) => err,
        None => return 0,
    };
    let last_error_length = last_error_length();

    if buffer.is_null() {
        *length = last_error_length;
        return -1;
    }

    // if passed in buffer is not big enough, return the error length so client can pass in a
    // bigger buffer
    if last_error_length >= *length {
        *length = last_error_length;
        return -1;
    }

    let buffer = slice::from_raw_parts_mut(buffer as *mut u8, *length as usize);

    ptr::copy_nonoverlapping(last_error.as_ptr(), buffer.as_mut_ptr(), last_error.len());

    // Add a trailing null so people using the string as a `char *` don't
    // accidentally read into garbage.
    buffer[last_error.len()] = 0;

    last_error.len() as c_int
}
