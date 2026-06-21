#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_packets(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(ParseError::Empty);
    }
    let mut values: Vec<u16> = Vec::with_capacity(max_items.min(1024));
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;
    let mut count: usize = 0;
    for part in trimmed.split(',') {
        let part = part.trim();
        if part.is_empty() {
            continue;
        }
        if count >= max_items {
            return Err(ParseError::TooMany);
        }
        let val: u16 = part.parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
        count += 1;
    }
    Ok(values)
}
