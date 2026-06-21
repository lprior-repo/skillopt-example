use repair_csv_quote_mixed::{parse_quotes, ParseError};

#[test]
fn parses_values() {
    assert_eq!(parse_quotes("1,2,3", 4), Ok(vec![1, 2, 3]));
}
#[test]
fn rejects_empty() {
    assert_eq!(parse_quotes("", 4), Err(ParseError::Empty));
}
#[test]
fn rejects_invalid() {
    assert_eq!(parse_quotes("1,nope", 4), Err(ParseError::Invalid));
}
#[test]
fn rejects_too_many() {
    assert_eq!(parse_quotes("1,2,3", 2), Err(ParseError::TooMany));
}
