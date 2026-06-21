use repair_frame_encoder::{encode_frame, FrameError};

#[test]
fn encodes_length_prefix() {
    assert_eq!(encode_frame(b"abc", 8), Ok(vec![0, 0, 0, 3, b'a', b'b', b'c']));
}

#[test]
fn rejects_payload_over_limit() {
    assert_eq!(encode_frame(b"abcdef", 3), Err(FrameError::PayloadTooLarge));
}
