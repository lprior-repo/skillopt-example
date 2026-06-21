use repair_checked_average::{average, AverageError};

#[test]
fn averages_values() {
    assert_eq!(average(&[2, 4, 6]), Ok(4));
}

#[test]
fn rejects_empty_slice() {
    assert_eq!(average(&[]), Err(AverageError::Empty));
}

#[test]
fn detects_overflow() {
    assert_eq!(average(&[u32::MAX, 1]), Err(AverageError::Overflow));
}
