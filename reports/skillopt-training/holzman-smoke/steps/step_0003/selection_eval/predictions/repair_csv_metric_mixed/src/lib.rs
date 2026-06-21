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

    let items: Vec<&str> = input.split(',').map(|s| s.trim()).collect();

    if items.len() > max_items {
        return Err(ParseError::TooMany);
    }

    let mut values = Vec::with_capacity(items.len());
    for part in &items {
        match part.parse::<u16>() {
            Ok(v) => values.push(v),
            Err(_) => return Err(ParseError::Invalid),
        }
    }

    Ok(values)
}
