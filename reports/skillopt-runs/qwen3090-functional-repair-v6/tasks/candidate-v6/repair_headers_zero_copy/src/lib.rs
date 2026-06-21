use std::borrow::Cow;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HeaderParseError {
    Empty,
    InvalidLine,
    EmptyName,
    TooMany,
    Allocation,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Header<'a> {
    pub name: Cow<'a, str>,
    pub value: Cow<'a, str>,
}

pub fn parse_headers(input: &str, max_headers: usize) -> Result<Vec<Header<'_>>, HeaderParseError> {
    if input.is_empty() {
        return Err(HeaderParseError::Empty);
    }

    let mut headers = Vec::new();
    headers.try_reserve(max_headers).map_err(|_| HeaderParseError::Allocation)?;

    for line in input.lines() {
        let (name, value) = line.split_once(':').ok_or(HeaderParseError::InvalidLine)?;
        let trimmed_name = name.trim();
        if trimmed_name.is_empty() {
            return Err(HeaderParseError::EmptyName);
        }
        if headers.len() >= max_headers {
            return Err(HeaderParseError::TooMany);
        }
        headers.push(Header {
            name: Cow::Borrowed(trimmed_name),
            value: Cow::Borrowed(value.trim()),
        });
    }

    Ok(headers)
}
