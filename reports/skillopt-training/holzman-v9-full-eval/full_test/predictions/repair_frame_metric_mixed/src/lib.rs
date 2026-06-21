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
    let len: u32 = payload.len().try_into().map_err(|_| FrameError::Overflow)?;
    let total = 4usize
        .checked_add(len as usize)
        .ok_or(FrameError::Overflow)?;
    let mut out = Vec::new();
    out.try_reserve(total).map_err(|_| FrameError::Allocation)?;
    out.extend_from_slice(&len.to_be_bytes());
    out.extend_from_slice(payload);
    Ok(out)
}
