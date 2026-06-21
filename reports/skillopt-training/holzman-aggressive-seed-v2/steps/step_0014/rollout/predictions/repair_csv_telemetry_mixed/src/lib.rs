#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_telemetrys(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.trim().is_empty() {
        return Err(ParseError::Empty);
    }
    let mut values: Vec<u16> = Vec::new();
    for part in input.split(',') {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            return Err(ParseError::Empty);
        }
        let val = trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    if values.len() > max_items {
        return Err(ParseError::TooMany);
    }
    Ok(values)
}
