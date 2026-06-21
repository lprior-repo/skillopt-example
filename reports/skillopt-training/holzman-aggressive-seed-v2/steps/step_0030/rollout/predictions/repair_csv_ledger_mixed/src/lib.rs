#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseError {
    Empty,
    Invalid,
    TooMany,
    Allocation,
}

pub fn parse_ledgers(input: &str, max_items: usize) -> Result<Vec<u16>, ParseError> {
    if input.trim().is_empty() {
        return Err(ParseError::Empty);
    }

    let mut values: Vec<u16> = Vec::new();
    values
        .try_reserve(max_items)
        .map_err(|_| ParseError::Allocation)?;

    let mut remaining = input;
    let mut count: usize = 0;

    loop {
        let (head, tail) = match remaining.split_once(',') {
            Some(pair) => pair,
            None => {
                let part = remaining.trim();
                if part.is_empty() {
                    break;
                }
                let val: u16 = part.parse().map_err(|_| ParseError::Invalid)?;
                values.push(val);
                break;
            }
        };

        let part = head.trim();
        if part.is_empty() {
            break;
        }

        let val: u16 = part.parse().map_err(|_| ParseError::Invalid)?;
        values.push(val);
        count += 1;

        if count >= max_items {
            if tail.trim().is_empty() {
                break;
            }
            return Err(ParseError::TooMany);
        }

        remaining = tail;
    }

    Ok(values)
}
