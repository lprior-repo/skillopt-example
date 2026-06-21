pub fn copy_prefix(input: &[u8], len: usize) -> Option<Vec<u8>> {
    if len > input.len() {
        return None;
    }
    Some(input[..len].to_vec())
}
