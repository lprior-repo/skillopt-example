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
    let mut remaining = input;
    loop {
        let (token, rest) = match remaining.split_once(',') {
            Some(pair) => pair,
            None => {
                let token = remaining.trim();
                if token.is_empty() {
                    return Err(ParseError::Invalid);
                }
                let val: u16 = token.parse().map_err(|_| ParseError::Invalid)?;
                values.push(val);
                break;
            }
        };
        let trimmed = token.trim();
        if trimmed.is_empty() {
            return Err(ParseError::Invalid);
        }
        let val: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
        if values.len() > max_items {
            return Err(ParseError::TooMany);
        }
        remaining = rest;
    }
    if values.len() > max_items {
        return Err(ParseError::TooMany);
    }
    Ok(values)
}
