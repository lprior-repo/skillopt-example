#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_sensors(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let parts: Vec<&str> = input.split(',').collect();
    if parts.is_empty() || (parts.len() == 1 && parts[0].trim().is_empty()) {
        return Err(ParseError::Empty);
    }
    let mut values: Vec<u16> = Vec::with_capacity(parts.len());
    for part in parts {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            return Err(ParseError::Empty);
        }
        let val: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    if values.len() > max_items {
        return Err(ParseError::TooMany);
    }
    Ok(values)
}
