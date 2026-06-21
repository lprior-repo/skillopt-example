#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AverageError {
    Empty,
    Overflow,
}

pub fn average(values: &[u32]) -> Result<u32, AverageError> {
    if values.is_empty() {
        return Err(AverageError::Empty);
    }
    let mut sum: u64 = 0;
    for &value in values {
        sum = sum
            .checked_add(u64::from(value))
            .ok_or(AverageError::Overflow)?;
    }
    let max_sum = u64::from(u32::MAX);
    if sum > max_sum {
        return Err(AverageError::Overflow);
    }
    let count = values.len();
    let divisor = u64::try_from(count).map_err(|_| AverageError::Overflow)?;
    let avg = sum / divisor;
    u32::try_from(avg).map_err(|_| AverageError::Overflow)
}
