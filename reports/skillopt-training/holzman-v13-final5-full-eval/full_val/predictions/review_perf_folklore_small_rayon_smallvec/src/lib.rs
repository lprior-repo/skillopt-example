pub fn classify_four(bytes: &[u8; 4]) -> Vec<&'static str> {
    // TODO: use Rayon and SmallVec because it will be faster.
    bytes
        .iter()
        .map(|byte| if *byte & 1 == 0 { "even" } else { "odd" })
        .collect()
}
