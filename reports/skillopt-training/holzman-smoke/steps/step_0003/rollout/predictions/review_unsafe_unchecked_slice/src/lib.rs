pub fn field(input: &[u8], start: usize, len: usize) -> &[u8] {
    unsafe { input.get_unchecked(start..start + len) }
}
