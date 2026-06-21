use repair_csv_u16::{parse_numbers, ParseNumbersError};

#[test]
fn parses_valid_numbers() {
    assert_eq!(parse_numbers("1, 2,65535", 4), Ok(vec![1, 2, 65535]));
}

#[test]
fn rejects_empty_input() {
    assert_eq!(parse_numbers("", 4), Err(ParseNumbersError::Empty));
}

#[test]
fn rejects_invalid_input_without_panic() {
    assert_eq!(parse_numbers("1,nope", 4), Err(ParseNumbersError::Invalid));
}

#[test]
fn enforces_max_items() {
    assert_eq!(parse_numbers("1,2,3", 2), Err(ParseNumbersError::TooMany));
}
