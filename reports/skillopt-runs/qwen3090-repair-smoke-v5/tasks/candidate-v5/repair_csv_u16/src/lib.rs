#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseNumbersError {
    Empty,
    Invalid,
    TooMany,
}

pub fn parse_numbers(input: &str, max_items: usize) -> Result<Vec<u16>, ParseNumbersError> {
    if input.is_empty() {
        return Err(ParseNumbersError::Empty);
    }
    let mut values = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseNumbersError::TooMany)?;
    for part in input.split(',') {
        if values.len() >= max_items {
            return Err(ParseNumbersError::TooMany);
        }
        let trimmed = part.trim();
        if trimmed.is_empty() {
            continue;
        }
        let value = trimmed
            .parse::<u16>()
            .map_err(|_| ParseNumbersError::Invalid)?;
        values.push(value);
    }
    if values.is_empty() {
        return Err(ParseNumbersError::Empty);
    }
    Ok(values)
}
