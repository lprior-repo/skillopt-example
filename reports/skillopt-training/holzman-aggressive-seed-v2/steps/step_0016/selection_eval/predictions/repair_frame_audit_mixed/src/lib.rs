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
    let header_len: u32 = u32::try_from(4).map_err(|_| FrameError::Overflow)?;
    let payload_len: u32 = u32::try_from(payload.len()).map_err(|_| FrameError::Overflow)?;
    out.try_reserve(
        usize::try_from(header_len).map_err(|_| FrameError::Overflow)?
            + usize::try_from(payload_len).map_err(|_| FrameError::Overflow)?,
    )
    .map_err(|_| FrameError::Allocation)?;
    out.extend_from_slice(&payload_len.to_be_bytes());
    out.extend_from_slice(payload);
    Ok(out)
}
