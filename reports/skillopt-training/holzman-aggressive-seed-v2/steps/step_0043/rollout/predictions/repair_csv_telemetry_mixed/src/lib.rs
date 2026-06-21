#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_telemetrys(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }

    let count = input.split(',').count();
    if count > max_items {
        return Err(ParseError::TooMany);
    }

    let mut values = Vec::with_capacity(count);
    for part in input.split(',') {
        let trimmed = part.trim();
        let val = trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    Ok(values)
}
