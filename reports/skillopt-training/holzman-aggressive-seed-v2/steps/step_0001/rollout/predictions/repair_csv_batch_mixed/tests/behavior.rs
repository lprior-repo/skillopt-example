use repair_csv_batch_mixed::{parse_batchs, ParseError};

#[test]
fn parses_values() {
    assert_eq!(parse_batchs("1,2,3", 4), Ok(vec![1, 2, 3]));
}
#[test]
fn rejects_empty() {
    assert_eq!(parse_batchs("", 4), Err(ParseError::Empty));
}
#[test]
fn rejects_invalid() {
    assert_eq!(parse_batchs("1,nope", 4), Err(ParseError::Invalid));
}
#[test]
fn rejects_too_many() {
    assert_eq!(parse_batchs("1,2,3", 2), Err(ParseError::TooMany));
}
