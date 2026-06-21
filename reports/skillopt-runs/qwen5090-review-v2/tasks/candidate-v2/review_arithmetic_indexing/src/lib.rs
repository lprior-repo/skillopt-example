pub fn read_window(buf: &[u8], offset: u32, len: u32) -> &[u8] {
    let start = offset as usize;
    let end = start + len as usize;
    &buf[start..end]
}
