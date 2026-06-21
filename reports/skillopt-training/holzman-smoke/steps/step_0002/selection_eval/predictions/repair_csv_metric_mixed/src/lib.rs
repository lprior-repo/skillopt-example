#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
}

pub fn parse_metrics(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }
    let values: Vec<u16> = input
        .split(',')
        .map(|part| part.trim().parse::<u16>().map_err(|_| ParseError::Invalid))
        .collect::<Result<_, _>>()?;
    if values.len() > max_items {
        return Err(ParseError::TooMany);
    }
    Ok(values)
}
