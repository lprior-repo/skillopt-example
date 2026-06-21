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
    let len: u32 = u32::try_from(payload.len()).map_err(|_| FrameError::Overflow)?;
    let payload_len = usize::try_from(len).map_err(|_| FrameError::Overflow)?;
    let capacity = payload_len.checked_add(4).ok_or(FrameError::Overflow)?;
    let mut out = Vec::with_capacity(capacity);
    out.extend_from_slice(&len.to_be_bytes());
    out.extend_from_slice(payload);
    Ok(out)
}
