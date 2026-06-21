#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_audits(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.trim().is_empty() {
        return Err(ParseError::Empty);
    }

    let fields: Vec<&str> = input
        .split(',')
        .map(|s| s.trim())
        .filter(|s| !s.is_empty())
        .collect();

    if fields.len() > max_items {
        return Err(ParseError::TooMany);
    }

    let mut values = Vec::new();
    values
        .try_reserve(fields.len())
        .map_err(|_| ParseError::Allocation)?;

    for field in fields {
        let v: u16 = field.parse().map_err(|_| ParseError::Invalid)?;
        values.push(v);
    }

    Ok(values)
}
