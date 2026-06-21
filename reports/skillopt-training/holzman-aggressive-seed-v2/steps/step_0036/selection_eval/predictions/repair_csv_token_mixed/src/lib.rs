#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_tokens(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(ParseError::Empty);
    }
    let tokens: Vec<&str> = trimmed.split(',').collect();
    if tokens.len() > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values: Vec<u16> = Vec::new();
    if let Err(_) = values.try_reserve(tokens.len()) {
        return Err(ParseError::Allocation);
    }
    for part in tokens {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            return Err(ParseError::Invalid);
        }
        let val: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    Ok(values)
}
