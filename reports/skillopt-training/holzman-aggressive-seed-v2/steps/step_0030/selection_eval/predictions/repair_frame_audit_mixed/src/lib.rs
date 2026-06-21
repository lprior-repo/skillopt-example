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
    let len: u32 = payload
        .len()
        .try_into()
        .map_err(|_| FrameError::PayloadTooLarge)?;
    let header: usize = 4;
    let capacity = header
        .checked_add(payload.len())
        .ok_or(FrameError::Overflow)?;
    let mut out = Vec::with_capacity(capacity);
    out.try_reserve(capacity)
        .map_err(|_| FrameError::Allocation)?;
    out.extend_from_slice(&len.to_be_bytes());
    out.extend_from_slice(payload);
    Ok(out)
}
