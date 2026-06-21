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
    let mut values: Vec<u16> = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;
    for part in trimmed.split(',') {
        let part = part.trim();
        if part.is_empty() {
            return Err(ParseError::Invalid);
        }
        let val: u16 = part.parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
        if values.len() > max_items {
            return Err(ParseError::TooMany);
        }
    }
    Ok(values)
}
