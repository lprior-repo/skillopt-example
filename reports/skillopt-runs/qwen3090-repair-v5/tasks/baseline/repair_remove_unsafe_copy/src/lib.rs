pub fn copy_prefix(input: &[u8], len: usize) -> Option<Vec<u8>> {
    if len > input.len() {
        return None;
    }
    let mut out = vec![0u8; len];
    out.copy_from_slice(&input[..len]);
    Some(out)
}
