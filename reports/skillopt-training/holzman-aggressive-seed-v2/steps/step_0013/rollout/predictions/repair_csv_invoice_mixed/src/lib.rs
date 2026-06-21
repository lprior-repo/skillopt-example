#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_invoices(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
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
        let part = part.trim();
        if part.is_empty() {
            return Err(ParseError::Invalid);
        }
        let n = part.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        values.push(n);
    }
    Ok(values)
}
