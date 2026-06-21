#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_shards(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }

    if max_items == 0 {
        return Err(ParseError::TooMany);
    }

    let mut values = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;

    let mut parts_count: usize = 0;

    for part in input.split(',') {
        let trimmed = part.trim();
        let value: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        parts_count = parts_count.checked_add(1).ok_or(ParseError::TooMany)?;
        if parts_count > max_items {
            return Err(ParseError::TooMany);
        }
        values.push(value);
    }

    Ok(values)
}
