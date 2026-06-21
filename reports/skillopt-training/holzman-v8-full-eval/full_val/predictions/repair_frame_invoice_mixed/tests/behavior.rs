use repair_frame_invoice_mixed::{encode_frame, FrameError};

#[test]
fn encodes() {
    assert_eq!(
        encode_frame(b"abc", 8),
        Ok(vec![0, 0, 0, 3, b'a', b'b', b'c'])
    );
}
#[test]
fn rejects_limit() {
    assert_eq!(encode_frame(b"abcdef", 3), Err(FrameError::PayloadTooLarge));
}
