#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RetryError {
    TooManyAttempts,
    Overflow,
}

pub fn retry_delays(attempts: usize, max_attempts: usize) -> Result<Vec<u64>, RetryError> {
    if attempts > max_attempts {
        return Err(RetryError::TooManyAttempts);
    }
    let mut out = Vec::new();
    for n in 0..attempts {
        if n >= 64 {
            return Err(RetryError::Overflow);
        }
        out.push(1u64 << n);
    }
    Ok(out)
}
