#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_samples(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(ParseError::Empty);
    }
    let parts: Vec<&str> = trimmed.split(',').collect();
    if parts.len() > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values = Vec::with_capacity(parts.len());
    values
        .try_reserve(parts.len())
        .map_err(|_| ParseError::Allocation)?;
    for part in parts {
        let val: u16 = part.trim().parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    Ok(values)
}
