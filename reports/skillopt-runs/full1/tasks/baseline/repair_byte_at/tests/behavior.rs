use repair_byte_at::byte_at;

#[test]
fn returns_byte_when_in_bounds() {
    assert_eq!(byte_at(b"abc", 1), Some(b'b'));
}

#[test]
fn returns_none_when_out_of_bounds() {
    assert_eq!(byte_at(b"abc", 9), None);
}
