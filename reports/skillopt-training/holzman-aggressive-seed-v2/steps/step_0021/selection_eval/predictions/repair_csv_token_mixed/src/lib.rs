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

    let count = input.split(',').count();
    if count > max_items {
        return Err(ParseError::TooMany);
    }

    let mut values: Vec<u16> = Vec::new();
    values
        .try_reserve(count)
        .map_err(|_| ParseError::Allocation)?;

    for part in input.split(',') {
        let val: u16 = part.trim().parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }

    Ok(values)
}
