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
    let mut values: Vec<u16> = Vec::new();
    for part in trimmed.split(',') {
        let val = part
            .trim()
            .parse::<u16>()
            .map_err(|_| ParseError::Invalid)?;
        if values.len() >= max_items {
            return Err(ParseError::TooMany);
        }
        values.push(val);
    }
    Ok(values)
}
