// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

use std::cell::RefCell;
use std::ffi::CString;
use std::os::raw::{c_char, c_int};

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
pub unsafe extern "C" fn libra_strerror() -> *const c_char {
    let last_error = match take_last_error() {
        Some(err) => err,
        None => return std::ptr::null_mut(),
    };

    let null_terminated = match CString::new(last_error.as_str()) {
        Ok(res) => res,
        _ => return std::ptr::null_mut(),
    };

    let error = null_terminated.into_boxed_c_str();
    (*Box::into_raw(error)).as_ptr()
}
