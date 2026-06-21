#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_metrics(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(ParseError::Empty);
    }

    let mut values = Vec::with_capacity(max_items);
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;

    for part in trimmed.split(',') {
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        let n = part
            .trim()
            .parse::<u16>()
            .map_err(|_| ParseError::Invalid)?;
        values.push(n);
    }

    Ok(values)
}
