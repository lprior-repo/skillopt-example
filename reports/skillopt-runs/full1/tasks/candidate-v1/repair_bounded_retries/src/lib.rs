#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RetryError {
    TooManyAttempts,
    Overflow,
}

pub fn retry_delays(attempts: usize, max_attempts: usize) -> Result<Vec<u64>, RetryError> {
    let mut out = Vec::new();
    for n in 0..attempts {
        out.push(1u64 << n);
    }
    Ok(out)
}
