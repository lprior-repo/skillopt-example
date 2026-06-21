#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_samples(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }

    let mut values = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;

    for part in input.split(',') {
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        let v = part
            .trim()
            .parse::<u16>()
            .map_err(|_| ParseError::Invalid)?;
        values.push(v);
    }

    Ok(values)
}
