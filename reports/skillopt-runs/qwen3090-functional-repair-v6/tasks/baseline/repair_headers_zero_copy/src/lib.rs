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

    let mut headers = Vec::with_capacity(max_headers);

    for line in input.lines() {
        if headers.len() >= max_headers {
            return Err(HeaderParseError::TooMany);
        }

        let colon_pos = line.find(':').ok_or(HeaderParseError::InvalidLine)?;
        let name = line[..colon_pos].trim();
        let value = line[colon_pos + 1..].trim();

        if name.is_empty() {
            return Err(HeaderParseError::EmptyName);
        }

        headers.push(Header {
            name: Cow::Borrowed(name),
            value: Cow::Borrowed(value),
        });
    }

    Ok(headers)
}
