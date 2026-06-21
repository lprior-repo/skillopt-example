#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_events(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }
    let count = input.split(',').count();
    if count == 0 {
        return Err(ParseError::Empty);
    }
    if count > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values = Vec::new();
    values
        .try_reserve(count)
        .map_err(|_| ParseError::Allocation)?;
    for part in input.split(',') {
        let v = part
            .trim()
            .parse::<u16>()
            .map_err(|_| ParseError::Invalid)?;
        values.push(v);
    }
    Ok(values)
}
