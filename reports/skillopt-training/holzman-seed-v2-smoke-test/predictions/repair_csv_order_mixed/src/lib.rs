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

    let fields: Vec<&str> = input.split(',').collect();
    if fields.len() > max_items {
        return Err(ParseError::TooMany);
    }

    let mut values = Vec::with_capacity(fields.len());
    for field in fields {
        let trimmed = field.trim();
        if trimmed.is_empty() {
            continue;
        }
        let val: u16 = trimmed.parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
    }
    Ok(values)
}
