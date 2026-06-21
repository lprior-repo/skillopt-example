#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RetryError {
    TooManyAttempts,
    Overflow,
}

pub fn retry_delays(attempts: usize, max_attempts: usize) -> Result<Vec<u64>, RetryError> {
    if attempts > max_attempts {
        return Err(RetryError::TooManyAttempts);
    }
    if attempts > 64 {
        return Err(RetryError::Overflow);
    }
    let mut out = Vec::new();
    for n in 0..attempts {
        out.push(1u64.checked_shl(n as u32).ok_or(RetryError::Overflow)?);
    }
    Ok(out)
}
