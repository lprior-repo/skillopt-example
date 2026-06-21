use repair_bounded_retries::{retry_delays, RetryError};

#[test]
fn builds_bounded_delays() {
    assert_eq!(retry_delays(4, 8), Ok(vec![1, 2, 4, 8]));
}

#[test]
fn rejects_attempts_above_max() {
    assert_eq!(retry_delays(9, 8), Err(RetryError::TooManyAttempts));
}

#[test]
fn rejects_shift_overflow() {
    assert_eq!(retry_delays(65, 65), Err(RetryError::Overflow));
}
