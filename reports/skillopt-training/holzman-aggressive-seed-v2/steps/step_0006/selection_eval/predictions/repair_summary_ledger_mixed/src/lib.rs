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
    let mut count: u64 = 0;
    for line in input.lines() {
        let (name, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let _name = name.trim();
        let _value_str = value_str.trim();
        let value: u64 = _value_str.parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
    }
    if count as usize > max_rows {
        return Err(SummaryError::TooMany);
    }
    let average: u64 = total / count;
    Ok(Summary {
        count: u32::try_from(count).map_err(|_| SummaryError::Overflow)?,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
