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
        sum = sum.checked_add(*value as u64).ok_or(AverageError::Overflow)?;
        if sum > u32::MAX as u64 {
            return Err(AverageError::Overflow);
        }
    }
    Ok((sum / values.len() as u64) as u32)
}
