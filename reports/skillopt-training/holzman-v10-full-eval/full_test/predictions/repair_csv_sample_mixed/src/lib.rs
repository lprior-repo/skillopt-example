#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_samples(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(ParseError::Empty);
    }
    let mut values: Vec<u16> = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;
    for part in trimmed.split(',') {
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        let v: u16 = part.trim().parse().map_err(|_| ParseError::Invalid)?;
        values.push(v);
    }
    Ok(values)
}
