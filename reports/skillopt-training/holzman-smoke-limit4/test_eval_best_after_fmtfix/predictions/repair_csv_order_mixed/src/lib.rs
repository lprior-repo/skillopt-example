#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_orders(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let mut values = Vec::with_capacity(max_items.min(input.split(',').count()));

    for part in input.split(',') {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            continue;
        }
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        values.push(trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?);
    }

    if values.is_empty() {
        return Err(ParseError::Empty);
    }

    Ok(values)
}
