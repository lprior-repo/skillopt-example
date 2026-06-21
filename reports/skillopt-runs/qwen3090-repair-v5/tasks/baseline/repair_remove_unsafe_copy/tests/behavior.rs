use repair_remove_unsafe_copy::copy_prefix;

#[test]
fn copies_prefix() {
    assert_eq!(copy_prefix(b"abcdef", 3), Some(vec![b'a', b'b', b'c']));
}

#[test]
fn rejects_oversized_len() {
    assert_eq!(copy_prefix(b"abc", 4), None);
}
