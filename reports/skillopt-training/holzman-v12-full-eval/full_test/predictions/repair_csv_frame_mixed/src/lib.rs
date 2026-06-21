#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_frames(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let parts: Vec<&str> = input
        .split(',')
        .map(|p| p.trim())
        .filter(|s| !s.is_empty())
        .collect();

    if parts.is_empty() {
        return Err(ParseError::Empty);
    }

    let count = parts.len();

    if count > max_items {
        return Err(ParseError::TooMany);
    }

    let mut out: Vec<u16> = Vec::new();
    out.try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;

    for part in parts {
        let val: u16 = part.parse().map_err(|_| ParseError::Invalid)?;
        out.push(val);
    }

    Ok(out)
}
