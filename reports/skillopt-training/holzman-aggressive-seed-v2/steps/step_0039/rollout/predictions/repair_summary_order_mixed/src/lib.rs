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
    let mut total: u64 = 0;
    let mut count: u64 = 0;
    for line in input.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let Some((name, value_str)) = trimmed.split_once(',') else {
            return Err(SummaryError::Invalid);
        };
        let name = name.trim();
        let value_str = value_str.trim();
        if name.is_empty() || value_str.is_empty() {
            return Err(SummaryError::Invalid);
        }
        let value: u64 = value_str.parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    let max_rows_u64 = u64::try_from(max_rows).unwrap_or(u64::MAX);
    if count > max_rows_u64 {
        return Err(SummaryError::TooMany);
    }
    let average = total.checked_div(count).ok_or(SummaryError::Invalid)?;
    let count_u32 = u32::try_from(count).map_err(|_| SummaryError::Overflow)?;
    Ok(Summary {
        count: count_u32,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
