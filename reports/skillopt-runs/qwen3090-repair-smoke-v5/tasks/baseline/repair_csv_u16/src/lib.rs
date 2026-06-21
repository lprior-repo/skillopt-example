#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseNumbersError {
    Empty,
    Invalid,
    TooMany,
}

pub fn parse_numbers(input: &str, max_items: usize) -> Result<Vec<u16>, ParseNumbersError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(ParseNumbersError::Empty);
    }
    let mut values = Vec::with_capacity(max_items);
    for part in trimmed.split(',') {
        if values.len() >= max_items {
            return Err(ParseNumbersError::TooMany);
        }
        let num = part
            .trim()
            .parse::<u16>()
            .map_err(|_| ParseNumbersError::Invalid)?;
        values.push(num);
    }
    Ok(values)
}
