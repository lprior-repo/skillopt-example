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
    if max_items == 0 {
        return Err(ParseError::TooMany);
    }

    let non_empty_count = input.split(',').filter(|p| !p.trim().is_empty()).count();
    if non_empty_count > max_items {
        return Err(ParseError::TooMany);
    }

    let mut values = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;

    for part in input.split(',') {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            continue;
        }
        values.push(trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?);
    }

    Ok(values)
}
