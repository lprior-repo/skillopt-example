use repair_csv_packet_mixed::{parse_packets, ParseError};

#[test]
fn parses_values() {
    assert_eq!(parse_packets("1,2,3", 4), Ok(vec![1, 2, 3]));
}
#[test]
fn rejects_empty() {
    assert_eq!(parse_packets("", 4), Err(ParseError::Empty));
}
#[test]
fn rejects_invalid() {
    assert_eq!(parse_packets("1,nope", 4), Err(ParseError::Invalid));
}
#[test]
fn rejects_too_many() {
    assert_eq!(parse_packets("1,2,3", 2), Err(ParseError::TooMany));
}
