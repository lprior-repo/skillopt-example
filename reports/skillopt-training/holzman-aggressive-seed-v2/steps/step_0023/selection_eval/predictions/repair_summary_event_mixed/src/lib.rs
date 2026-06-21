#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SummaryError {
    Empty,
    Invalid,
    TooMany,
    Overflow,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Summary {
    pub count: u32,
    pub total: u64,
    pub average: u64,
}

pub fn summarize_metrics(input: &str, max_rows: usize) -> Result<Summary, SummaryError> {
    if input.is_empty() {
        return Err(SummaryError::Empty);
    }
    let mut total: u64 = 0;
    let mut count: usize = 0;
    for line in input.lines() {
        if line.is_empty() {
            continue;
        }
        let (key, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let _key = key.trim();
        let _value_str = value_str.trim();
        let value: u64 = _value_str.parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
        if count > max_rows {
            return Err(SummaryError::TooMany);
        }
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    let average = total / count as u64;
    Ok(Summary {
        count: count as u32,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
