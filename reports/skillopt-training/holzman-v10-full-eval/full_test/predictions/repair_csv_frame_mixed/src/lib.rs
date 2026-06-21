#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_frames(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.trim().is_empty() {
        return Err(ParseError::Empty);
    }

    let mut values = Vec::with_capacity(max_items);
    if max_items > 0 {
        values
            .try_reserve(max_items)
            .map_err(|_| ParseError::Allocation)?;
    }

    let mut count: usize = 0;

    for part in input.split(',') {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            continue;
        }

        let val: u16 = trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?;

        count = count.checked_add(1).ok_or(ParseError::TooMany)?;

        if count > max_items {
            return Err(ParseError::TooMany);
        }

        values.push(val);
    }

    if values.is_empty() {
        return Err(ParseError::Empty);
    }

    Ok(values)
}
