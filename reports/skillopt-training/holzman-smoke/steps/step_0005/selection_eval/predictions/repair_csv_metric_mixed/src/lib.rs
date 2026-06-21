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
    let mut values = Vec::with_capacity(count);
    for part in trimmed.split(',') {
        let val: u16 = part.trim().parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    Ok(values)
}
