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
    if max_items == 0 {
        return Err(ParseError::TooMany);
    }
    let mut values = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;
    for part in input.split(',') {
        let trimmed = part.trim();
        let n: u16 = trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        values.push(n);
    }
    if values.is_empty() {
        return Err(ParseError::Empty);
    }
    Ok(values)
}
