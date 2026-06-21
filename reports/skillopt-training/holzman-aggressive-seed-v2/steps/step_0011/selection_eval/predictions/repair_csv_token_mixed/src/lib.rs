#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_tokens(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }

    let mut values = Vec::new();
    for part in input.split(',') {
        let trimmed = part.trim();
        let parsed = trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        values.push(parsed);
    }

    Ok(values)
}
