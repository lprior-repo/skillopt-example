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
    let mut values: Vec<u16> = Vec::with_capacity(max_items);
    for part in input.split(',') {
        let trimmed = part.trim();
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        match trimmed.parse::<u16>() {
            Ok(v) => values.push(v),
            Err(_) => return Err(ParseError::Invalid),
        }
    }
    Ok(values)
}
