#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseNumbersError {
    Empty,
    Invalid,
    TooMany,
}

pub fn parse_numbers(input: &str, max_items: usize) -> Result<Vec<u16>, ParseNumbersError> {
    let parts: Vec<&str> = input.split(',').collect();
    let parts: Vec<&str> = parts.into_iter().filter(|p| !p.trim().is_empty()).collect();
    if parts.is_empty() {
        return Err(ParseNumbersError::Empty);
    }
    if parts.len() > max_items {
        return Err(ParseNumbersError::TooMany);
    }
    let mut values = Vec::with_capacity(parts.len());
    for part in parts {
        let trimmed = part.trim();
        let n: u16 = trimmed.parse().map_err(|_| ParseNumbersError::Invalid)?;
        values.push(n);
    }
    Ok(values)
}
