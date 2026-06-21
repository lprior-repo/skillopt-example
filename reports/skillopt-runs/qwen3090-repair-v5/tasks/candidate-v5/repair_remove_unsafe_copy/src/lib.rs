pub fn copy_prefix(input: &[u8], len: usize) -> Option<Vec<u8>> {
    input.get(..len).map(|s| s.to_vec())
}
