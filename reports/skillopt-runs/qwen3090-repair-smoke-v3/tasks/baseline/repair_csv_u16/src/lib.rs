#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseNumbersError {
    Empty,
    Invalid,
    TooMany,
}

pub fn parse_numbers(input: &str, max_items: usize) -> Result<Vec<u16>, ParseNumbersError> {
    if input.trim().is_empty() {
        return Err(ParseNumbersError::Empty);
    }
    let mut values: Vec<u16> = Vec::with_capacity(max_items);
    for part in input.split(',') {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            return Err(ParseNumbersError::Empty);
        }
        let val: u16 = trimmed.parse().map_err(|_| ParseNumbersError::Invalid)?;
        values.push(val);
        if values.len() > max_items {
            return Err(ParseNumbersError::TooMany);
        }
    }
    if values.is_empty() {
        return Err(ParseNumbersError::Empty);
    }
    Ok(values)
}
