#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_routes(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let parts: Vec<&str> = input.split(',').collect();
    if parts.iter().all(|p| p.trim().is_empty()) {
        return Err(ParseError::Empty);
    }
    if parts.len() > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values = Vec::with_capacity(parts.len());
    for part in parts {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            continue;
        }
        let v = trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        values.push(v);
    }
    Ok(values)
}
