#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_tokens(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let parts: Vec<&str> = input.split(',').collect();
    let trimmed: Vec<&str> = parts.iter().map(|p| p.trim()).collect();
    if trimmed.iter().all(|p| p.is_empty()) {
        return Err(ParseError::Empty);
    }
    if trimmed.len() > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values = Vec::with_capacity(trimmed.len());
    values
        .try_reserve(trimmed.len())
        .map_err(|_| ParseError::Allocation)?;
    for part in trimmed {
        if part.is_empty() {
            continue;
        }
        let n: u16 = part.parse().map_err(|_| ParseError::Invalid)?;
        values.push(n);
    }
    Ok(values)
}
