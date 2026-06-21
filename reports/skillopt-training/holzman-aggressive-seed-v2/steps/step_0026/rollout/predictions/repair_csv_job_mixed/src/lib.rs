#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_jobs(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.is_empty() {
        return Err(ParseError::Empty);
    }

    let token_count = input
        .split(',')
        .filter(|part| !part.trim().is_empty())
        .count();

    if token_count > max_items {
        return Err(ParseError::TooMany);
    }

    let mut result = Vec::with_capacity(token_count);
    for part in input.split(',') {
        let trimmed = part.trim();
        if trimmed.is_empty() {
            continue;
        }
        match trimmed.parse::<u16>() {
            Ok(v) => result.push(v),
            Err(_) => return Err(ParseError::Invalid),
        }
    }

    if result.is_empty() {
        Err(ParseError::Empty)
    } else {
        Ok(result)
    }
}
