#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_metrics(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.trim().is_empty() {
        return Err(ParseError::Empty);
    }
    let parts: Vec<&str> = input.split(',').collect();
    if parts.len() > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values = Vec::with_capacity(parts.len());
    for part in parts {
        let trimmed = part.trim();
        let v: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        values.push(v);
    }
    Ok(values)
}
