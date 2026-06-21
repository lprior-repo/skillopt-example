#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_tokens(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.trim().is_empty() {
        return Err(ParseError::Empty);
    }
    let mut values: Vec<u16> = Vec::new();
    try_reserve(&mut values, max_items)?;
    for part in input.split(',') {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            continue;
        }
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        match trimmed.parse::<u16>() {
            Ok(v) => values.push(v),
            Err(_) => return Err(ParseError::Invalid),
        }
    }
    if values.is_empty() {
        return Err(ParseError::Empty);
    }
    Ok(values)
}

fn try_reserve(vec: &mut Vec<u16>, capacity: usize) -> Result<(), ParseError> {
    vec.try_reserve(capacity)
        .map_err(|_| ParseError::Allocation)
}
