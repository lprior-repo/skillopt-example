#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_audits(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let parts: Vec<&str> = input.split(',').collect();
    if parts.iter().all(|p| p.trim().is_empty()) {
        return Err(ParseError::Empty);
    }
    let mut values = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;
    for part in parts {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            continue;
        }
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        let v: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        values.push(v);
    }
    Ok(values)
}
