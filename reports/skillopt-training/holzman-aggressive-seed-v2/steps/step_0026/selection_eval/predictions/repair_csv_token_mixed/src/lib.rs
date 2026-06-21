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
    let count = input.split(',').count();
    if count > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values: Vec<u16> = Vec::with_capacity(count);
    values
        .try_reserve(count)
        .map_err(|_| ParseError::Allocation)?;
    for part in input.split(',') {
        let p = part.trim();
        if p.is_empty() {
            continue;
        }
        let v: u16 = p.parse().map_err(|_| ParseError::Invalid)?;
        values.push(v);
    }
    Ok(values)
}
