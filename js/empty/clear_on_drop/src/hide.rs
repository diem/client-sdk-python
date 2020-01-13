//! Prevent agressive code removal optimizations.
//!
//! The functions in this module "hide" a variable from the optimizer,
//! so that it believes the variable has been read and/or modified in
//! unpredictable ways, while in fact nothing happened.
//!
//! Inspired by/based on Linux kernel's `OPTIMIZER_HIDE_VAR`, which in
//! turn was based on the earlier `RELOC_HIDE` macro.

/// Make the optimizer believe the memory pointed to by `ptr` is read
/// and modified arbitrarily.
#[inline]
pub fn hide_mem<T: ?Sized>(ptr: &mut T) {
    hide_mem_impl(ptr);
}

/// Make the optimizer believe the pointer returned by this function is
/// possibly unrelated (except for the lifetime) to `ptr`.
#[inline]
pub fn hide_ptr<P>(mut ptr: P) -> P {
    hide_mem::<P>(&mut ptr);
    ptr
}

pub use self::impls::hide_mem_impl;

mod impls {
    use core::sync::atomic::{AtomicUsize, Ordering, ATOMIC_USIZE_INIT};

    #[inline(never)]
    pub fn hide_mem_impl<T: ?Sized>(ptr: *mut T) {
        static DUMMY: AtomicUsize = ATOMIC_USIZE_INIT;
        DUMMY.store(ptr as *mut u8 as usize, Ordering::Release);
    }
}

#[cfg(test)]
mod tests {
    struct Place {
        data: [u32; 4],
    }

    const DATA: [u32; 4] = [0x01234567, 0x89abcdef, 0xfedcba98, 0x76543210];

    #[test]
    fn hide_mem() {
        let mut place = Place { data: DATA };
        super::hide_mem(&mut place);
        assert_eq!(place.data, DATA);
    }

    #[test]
    fn hide_ptr() {
        let mut place = Place { data: DATA };
        let before = &mut place as *mut _;
        let after = super::hide_ptr(&mut place);
        assert_eq!(before, after as *mut _);
        assert_eq!(after.data, DATA);
    }
}
