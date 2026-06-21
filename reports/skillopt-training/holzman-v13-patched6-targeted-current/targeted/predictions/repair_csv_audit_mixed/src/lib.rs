#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_audits(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
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
        let trimmed = part.trim();
        let val: u16 = trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    Ok(values)
}
