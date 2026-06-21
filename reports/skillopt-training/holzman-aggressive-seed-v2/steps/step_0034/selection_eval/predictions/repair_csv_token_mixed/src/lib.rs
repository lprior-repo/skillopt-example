#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_tokens(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }
    let parts: Vec<&str> = input.split(',').map(|p| p.trim()).collect();
    if parts.len() > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values = Vec::with_capacity(parts.len());
    for part in parts {
        if part.is_empty() {
            return Err(ParseError::Invalid);
        }
        let v: u16 = part.parse().map_err(|_| ParseError::Invalid)?;
        values.push(v);
    }
    Ok(values)
}
