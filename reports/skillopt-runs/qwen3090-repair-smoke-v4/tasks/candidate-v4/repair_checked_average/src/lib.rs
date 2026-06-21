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
    for value in values {
        let val = u64::from(*value);
        let new_sum = sum.checked_add(val).ok_or(AverageError::Overflow)?;
        if new_sum > u64::from(u32::MAX) {
            return Err(AverageError::Overflow);
        }
        sum = new_sum;
    }
    let count = u64::try_from(values.len()).map_err(|_| AverageError::Overflow)?;
    let avg = sum / count;
    u32::try_from(avg).map_err(|_| AverageError::Overflow)
}
