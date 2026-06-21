#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_orders(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(ParseError::Empty);
    }
    let values: Vec<u16> = trimmed
        .split(',')
        .map(|part| part.trim().parse::<u16>().map_err(|_| ParseError::Invalid))
        .collect::<Result<Vec<u16>, ParseError>>()?;
    if values.len() > max_items {
        return Err(ParseError::TooMany);
    }
    Ok(values)
}
