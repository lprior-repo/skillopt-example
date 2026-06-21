#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_samples(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }
    let mut values: Vec<u16> = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;
    for part in input.split(',') {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            return Err(ParseError::Invalid);
        }
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        let val = trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    Ok(values)
}
