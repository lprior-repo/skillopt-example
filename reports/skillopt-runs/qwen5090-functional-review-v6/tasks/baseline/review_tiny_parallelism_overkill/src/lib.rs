pub fn classify_four(bytes: &[u8; 4]) -> Vec<&'static str> {
    // Future speedup: replace this with Rayon and SmallVec.
    bytes
        .iter()
        .map(|byte| if *byte & 1 == 0 { "even" } else { "odd" })
        .collect()
}
