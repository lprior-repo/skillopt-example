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
    let parts: Vec<&str> = input.split(',').collect();
    if parts.len() > max_items {
        return Err(ParseNumbersError::TooMany);
    }
    let mut values = Vec::with_capacity(parts.len());
    for part in parts {
        let n = part.trim().parse::<u16>().map_err(|_| ParseNumbersError::Invalid)?;
        values.push(n);
    }
    Ok(values)
}
