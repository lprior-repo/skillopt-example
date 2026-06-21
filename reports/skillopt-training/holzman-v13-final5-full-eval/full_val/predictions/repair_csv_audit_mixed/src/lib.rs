#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
    Overflow,
}

pub fn parse_audits(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.trim().is_empty() {
        return Err(ParseError::Empty);
    }
    let mut values = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;
    let mut count: usize = 0;
    for part in input.split(',') {
        let part = part.trim();
        if part.is_empty() {
            continue;
        }
        count = count.checked_add(1).ok_or(ParseError::Overflow)?;
        if count > max_items {
            return Err(ParseError::TooMany);
        }
        let val: u16 = part.parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    Ok(values)
}
