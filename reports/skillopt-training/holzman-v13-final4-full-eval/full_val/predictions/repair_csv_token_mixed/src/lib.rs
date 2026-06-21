#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_tokens(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() || input.trim().is_empty() {
        return Err(ParseError::Empty);
    }
    let mut values = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;
    for part in input.split(',') {
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        let val: u16 = part.trim().parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    Ok(values)
}
