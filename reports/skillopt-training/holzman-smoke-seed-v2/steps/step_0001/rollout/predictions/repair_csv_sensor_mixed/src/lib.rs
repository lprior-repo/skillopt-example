#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_sensors(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.trim().is_empty() {
        return Err(ParseError::Empty);
    }

    let mut values = Vec::with_capacity(max_items.min(1024));
    for part in input.split(',') {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            return Err(ParseError::Invalid);
        }
        let val: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        values.push(val);
    }
    Ok(values)
}
