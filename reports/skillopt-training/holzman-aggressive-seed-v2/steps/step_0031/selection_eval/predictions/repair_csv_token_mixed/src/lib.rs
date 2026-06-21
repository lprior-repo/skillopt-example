#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_tokens(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }

    let mut count: usize = 0;
    for ch in input.chars() {
        if ch == ',' {
            count = count.checked_add(1).ok_or(ParseError::TooMany)?;
        }
    }
    count = count.checked_add(1).ok_or(ParseError::TooMany)?;

    if count > max_items {
        return Err(ParseError::TooMany);
    }

    let mut values: Vec<u16> = Vec::new();
    values
        .try_reserve(count)
        .map_err(|_| ParseError::Allocation)?;

    for part in input.split(',') {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            return Err(ParseError::Invalid);
        }
        let val: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }

    Ok(values)
}
