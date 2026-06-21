#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_metrics(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }

    let item_count = input.split(',').count();
    if item_count > max_items {
        return Err(ParseError::TooMany);
    }

    let mut values = Vec::with_capacity(item_count);
    for part in input.split(',') {
        let trimmed = part.trim();
        match trimmed.parse::<u16>() {
            Ok(v) => values.push(v),
            Err(_) => return Err(ParseError::Invalid),
        }
    }

    Ok(values)
}
