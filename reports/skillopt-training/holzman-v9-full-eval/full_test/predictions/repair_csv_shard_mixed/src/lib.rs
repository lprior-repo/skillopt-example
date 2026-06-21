#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_shards(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(ParseError::Empty);
    }

    let values: Vec<u16> = trimmed.split(',').try_fold(Vec::new(), |mut acc, part| {
        if acc.len() == max_items {
            return Err(ParseError::TooMany);
        }
        let val: u16 = part
            .trim()
            .parse::<u16>()
            .map_err(|_| ParseError::Invalid)?;
        acc.push(val);
        Ok(acc)
    })?;

    Ok(values)
}
