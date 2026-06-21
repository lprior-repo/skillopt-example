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
    let total = 4usize
        .checked_add(payload.len())
        .ok_or(FrameError::Overflow)?;
    out.try_reserve(total).map_err(|_| FrameError::Allocation)?;
    out.extend_from_slice(
        &u32::try_from(payload.len())
            .map_err(|_| FrameError::Overflow)?
            .to_be_bytes(),
    );
    out.extend_from_slice(payload);
    Ok(out)
}
