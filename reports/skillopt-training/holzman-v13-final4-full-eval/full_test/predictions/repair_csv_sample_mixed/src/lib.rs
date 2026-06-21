#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
    Overflow,
}

pub fn parse_samples(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let parts: Vec<&str> = input.split(',').collect();
    if parts.is_empty() {
        return Err(ParseError::Empty);
    }
    let mut values = Vec::new();
    values
        .try_reserve(parts.len())
        .map_err(|_| ParseError::Allocation)?;
    let mut count: usize = 0;
    for part in parts {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            continue;
        }
        if count >= max_items {
            return Err(ParseError::TooMany);
        }
        let val: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
        count = count.checked_add(1).ok_or(ParseError::Overflow)?;
    }
    if values.is_empty() {
        return Err(ParseError::Empty);
    }
    Ok(values)
}
