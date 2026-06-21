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

    let count = trimmed.split(',').count();
    if count > max_items {
        return Err(ParseError::TooMany);
    }

    let mut values: Vec<u16> = Vec::new();
    values
        .try_reserve(count)
        .map_err(|_| ParseError::Allocation)?;

    for part in trimmed.split(',') {
        let val = part
            .trim()
            .parse::<u16>()
            .map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }

    Ok(values)
}
