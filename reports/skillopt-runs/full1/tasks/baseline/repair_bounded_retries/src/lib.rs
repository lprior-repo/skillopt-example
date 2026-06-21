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
        let shift = u32::try_from(n).map_err(|_| RetryError::Overflow)?;
        let delay = 1u64.checked_shl(shift).ok_or(RetryError::Overflow)?;
        out.push(delay);
    }
    Ok(out)
}
