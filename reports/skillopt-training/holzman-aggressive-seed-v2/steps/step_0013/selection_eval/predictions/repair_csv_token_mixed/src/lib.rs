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
    let mut values: Vec<u16> = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;
    let mut remaining = input;
    while !remaining.is_empty() {
        let (part, next) = match remaining.split_once(',') {
            Some(s) => s,
            None => (remaining, ""),
        };
        let trimmed = part.trim();
        if trimmed.is_empty() {
            return Err(ParseError::Invalid);
        }
        let val: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        values.push(val);
        remaining = next;
    }
    Ok(values)
}
