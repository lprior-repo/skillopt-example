#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AverageError {
    Empty,
    Overflow,
}

pub fn average(values: &[u32]) -> Result<u32, AverageError> {
    if values.is_empty() {
        return Err(AverageError::Empty);
    }
    let mut sum = 0u32;
    for value in values {
        sum = sum.checked_add(*value).ok_or(AverageError::Overflow)?;
    }
    Ok(sum / values.len() as u32)
}
