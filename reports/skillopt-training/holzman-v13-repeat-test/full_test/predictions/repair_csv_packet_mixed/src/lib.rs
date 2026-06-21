#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_packets(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }
    let parts: Vec<&str> = input.split(',').collect();
    if parts.len() == 0 {
        return Err(ParseError::Empty);
    }
    if parts.len() > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values: Vec<u16> = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;
    for part in parts {
        let trimmed = part.trim();
        let v: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        values.push(v);
    }
    Ok(values)
}
