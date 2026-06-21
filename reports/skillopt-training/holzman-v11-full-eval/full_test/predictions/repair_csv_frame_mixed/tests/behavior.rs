use repair_csv_frame_mixed::{parse_frames, ParseError};

#[test]
fn parses_values() {
    assert_eq!(parse_frames("1,2,3", 4), Ok(vec![1, 2, 3]));
}
#[test]
fn rejects_empty() {
    assert_eq!(parse_frames("", 4), Err(ParseError::Empty));
}
#[test]
fn rejects_invalid() {
    assert_eq!(parse_frames("1,nope", 4), Err(ParseError::Invalid));
}
#[test]
fn rejects_too_many() {
    assert_eq!(parse_frames("1,2,3", 2), Err(ParseError::TooMany));
}
