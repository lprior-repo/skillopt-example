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

    let parts: Vec<&str> = input.split(',').filter(|s| !s.trim().is_empty()).collect();

    if parts.is_empty() {
        return Err(ParseError::Empty);
    }

    if parts.len() > max_items {
        return Err(ParseError::TooMany);
    }

    let mut values: Vec<u16> = Vec::new();
    values
        .try_reserve(parts.len())
        .map_err(|_| ParseError::Allocation)?;

    for part in parts {
        let value = part
            .trim()
            .parse::<u16>()
            .map_err(|_| ParseError::Invalid)?;
        values.push(value);
    }

    Ok(values)
}
