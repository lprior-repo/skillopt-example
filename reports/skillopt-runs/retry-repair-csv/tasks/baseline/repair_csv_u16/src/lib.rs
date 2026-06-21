#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ParseNumbersError {
    Empty,
    Invalid,
    TooMany,
}

pub fn parse_numbers(input: &str, max_items: usize) -> Result<Vec<u16>, ParseNumbersError> {
    let values: Vec<u16> = input
        .split(',')
        .map(|part| part.trim().parse::<u16>().unwrap())
        .collect();
    Ok(values)
}
