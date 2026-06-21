#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_tokens(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let parts: Vec<&str> = input.split(',').collect();
    if parts.is_empty() || (parts.len() == 1 && parts[0].trim().is_empty()) {
        return Err(ParseError::Empty);
    }
    if parts.len() > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values = Vec::new();
    values
        .try_reserve(parts.len())
        .map_err(|_| ParseError::Allocation)?;
    for part in parts {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            return Err(ParseError::Empty);
        }
        let n: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        values.push(n);
    }
    Ok(values)
}
