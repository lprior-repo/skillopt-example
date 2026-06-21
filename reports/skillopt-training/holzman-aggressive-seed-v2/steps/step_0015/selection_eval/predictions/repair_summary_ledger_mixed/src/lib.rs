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
    let mut total = 0u64;
    let mut count: u64 = 0;
    for line in input.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let (name, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let name = name.trim();
        let value_str = value_str.trim();
        if name.is_empty() || value_str.is_empty() {
            return Err(SummaryError::Invalid);
        }
        let value: u64 = value_str.parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    let max_rows_u64 = u64::try_from(max_rows).map_err(|_| SummaryError::TooMany)?;
    if count > max_rows_u64 {
        return Err(SummaryError::TooMany);
    }
    let average = total / count;
    Ok(Summary {
        count: count as u32,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
