use std::borrow::Cow;
use repair_headers_zero_copy::{parse_headers, Header, HeaderParseError};

#[test]
fn parses_headers_as_borrowed_fields() {
    let input = "host: example.com\naccept: text/plain";
    assert_eq!(
        parse_headers(input, 4),
        Ok(vec![
            Header { name: Cow::Borrowed("host"), value: Cow::Borrowed("example.com") },
            Header { name: Cow::Borrowed("accept"), value: Cow::Borrowed("text/plain") },
        ])
    );
}

#[test]
fn rejects_empty_input() {
    assert_eq!(parse_headers("", 4), Err(HeaderParseError::Empty));
}

#[test]
fn rejects_invalid_line_without_panic() {
    assert_eq!(parse_headers("missing_separator", 4), Err(HeaderParseError::InvalidLine));
}

#[test]
fn rejects_empty_header_name() {
    assert_eq!(parse_headers(": value", 4), Err(HeaderParseError::EmptyName));
}

#[test]
fn enforces_header_limit() {
    assert_eq!(parse_headers("a: 1\nb: 2", 1), Err(HeaderParseError::TooMany));
}
