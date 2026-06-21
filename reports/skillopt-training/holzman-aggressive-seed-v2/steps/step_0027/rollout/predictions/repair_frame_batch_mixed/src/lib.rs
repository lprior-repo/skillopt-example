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
    let mut out = Vec::new();
    let header_size = 4usize;
    let payload_size = payload.len();
    let total = header_size
        .checked_add(payload_size)
        .ok_or(FrameError::Overflow)?;
    out.try_reserve(total).map_err(|_| FrameError::Allocation)?;
    let len: u32 = payload_size.try_into().map_err(|_| FrameError::Overflow)?;
    out.extend_from_slice(&len.to_be_bytes());
    out.extend_from_slice(payload);
    Ok(out)
}
