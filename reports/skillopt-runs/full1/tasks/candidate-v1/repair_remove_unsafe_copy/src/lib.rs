pub fn copy_prefix(input: &[u8], len: usize) -> Option<Vec<u8>> {
    if len > input.len() {
        return None;
    }
    let mut out = Vec::with_capacity(len);
    unsafe {
        out.set_len(len);
        std::ptr::copy_nonoverlapping(input.as_ptr(), out.as_mut_ptr(), len);
    }
    Some(out)
}
