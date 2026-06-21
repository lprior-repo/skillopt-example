#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_tokens(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.trim().is_empty() {
        return Err(ParseError::Empty);
    }

    let mut values = Vec::with_capacity(max_items);
    for part in input.split(',') {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            continue;
        }
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        let val = trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }

    Ok(values)
}
