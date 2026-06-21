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
    let values: Result<Vec<u16>, _> = input
        .split(',')
        .map(|part| {
            let trimmed = part.trim();
            if trimmed.is_empty() {
                return Err(ParseNumbersError::Empty);
            }
            trimmed
                .parse::<u16>()
                .map_err(|_| ParseNumbersError::Invalid)
        })
        .collect();
    let values = values?;
    if values.len() > max_items {
        return Err(ParseNumbersError::TooMany);
    }
    Ok(values)
}
