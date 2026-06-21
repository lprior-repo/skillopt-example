#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_audits(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.trim().is_empty() {
        return Err(ParseError::Empty);
    }

    let mut values = Vec::with_capacity(max_items);
    for part in input.split(',') {
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        let trimmed = part.trim();
        if trimmed.is_empty() {
            continue;
        }
        let val: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }

    if values.len() > max_items {
        return Err(ParseError::TooMany);
    }

    Ok(values)
}
