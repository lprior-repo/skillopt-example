#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FrameError {
    PayloadTooLarge,
    Allocation,
    Overflow,
}

pub fn encode_frame(payload: &[u8], max_payload: usize) -> Result<Vec<u8>, FrameError> {
    if payload.len() > max_payload {
        return Err(FrameError::PayloadTooLarge);
    }
    let header_size: usize = 4;
    let capacity = header_size
        .checked_add(payload.len())
        .ok_or(FrameError::Overflow)?;
    let mut out = Vec::new();
    out.try_reserve(capacity)
        .map_err(|_| FrameError::Allocation)?;
    let len = u32::try_from(payload.len()).map_err(|_| FrameError::Overflow)?;
    out.extend_from_slice(&len.to_be_bytes());
    out.extend_from_slice(payload);
    Ok(out)
}
