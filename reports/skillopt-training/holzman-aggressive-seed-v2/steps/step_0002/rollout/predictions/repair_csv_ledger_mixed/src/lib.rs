#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_ledgers(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(ParseError::Empty);
    }
    let parts: Vec<&str> = trimmed.split(',').collect();
    let len = parts.len();
    if len == 0 {
        return Err(ParseError::Empty);
    }
    let cap = len.checked_sub(1).unwrap_or(len);
    let mut values = Vec::with_capacity(len);
    if cap > 0 {
        values
            .try_reserve(cap)
            .map_err(|_| ParseError::Allocation)?;
    }
    for part in parts {
        let t = part.trim();
        if t.is_empty() {
            continue;
        }
        let v = t.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        values.push(v);
    }
    if values.len() > max_items {
        return Err(ParseError::TooMany);
    }
    Ok(values)
}
