#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AverageError {
    Empty,
    Overflow,
}

pub fn average(values: &[u32]) -> Result<u32, AverageError> {
    let mut sum = 0u32;
    for value in values {
        sum += *value;
    }
    Ok(sum / values.len() as u32)
}
