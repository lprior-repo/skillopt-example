#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_tokens(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(ParseError::Empty);
    }

    let parts: Vec<&str> = trimmed.split(',').filter(|p| !p.is_empty()).collect();
    let token_count = parts.len();

    if token_count == 0 {
        return Err(ParseError::Empty);
    }
    if token_count > max_items {
        return Err(ParseError::TooMany);
    }

    let mut values = Vec::with_capacity(token_count);
    for part in parts {
        let val = part
            .trim()
            .parse::<u16>()
            .map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    Ok(values)
}
