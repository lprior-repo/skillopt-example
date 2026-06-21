#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_metrics(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(ParseError::Empty);
    }
    let count = trimmed.split(',').count();
    if count > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values: Vec<u16> = Vec::with_capacity(count);
    values
        .try_reserve(count)
        .map_err(|_| ParseError::Allocation)?;
    for part in trimmed.split(',') {
        let part = part.trim();
        if part.is_empty() {
            return Err(ParseError::Invalid);
        }
        let val: u16 = part.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    Ok(values)
}
