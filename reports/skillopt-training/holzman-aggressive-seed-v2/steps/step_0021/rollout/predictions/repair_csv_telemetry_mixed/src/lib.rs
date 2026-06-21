#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_telemetrys(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }
    let comma_count = input.chars().filter(|&c| c == ',').count();
    let item_count = comma_count.checked_add(1).ok_or(ParseError::Allocation)?;
    if item_count > max_items {
        return Err(ParseError::TooMany);
    }
    let mut values = Vec::with_capacity(item_count);
    values
        .try_reserve(item_count)
        .map_err(|_| ParseError::Allocation)?;
    let mut rest = Some(input);
    while let Some(s) = rest {
        let (first, remaining) = s.split_once(',').unwrap_or((s, ""));
        let trimmed = first.trim();
        let val = trimmed.parse::<u16>().map_err(|_| ParseError::Invalid)?;
        values.push(val);
        rest = if remaining.is_empty() {
            None
        } else {
            Some(remaining)
        };
    }
    Ok(values)
}
