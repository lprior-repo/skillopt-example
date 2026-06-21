#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SummaryError {
    Empty,
    Invalid,
    TooMany,
    Overflow,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Summary {
    pub count: u64,
    pub total: u64,
    pub average: u64,
}

pub fn summarize_metrics(input: &str, max_rows: usize) -> Result<Summary, SummaryError> {
    if input.is_empty() {
        return Err(SummaryError::Empty);
    }
    let max_rows_u64 = u64::try_from(max_rows).unwrap_or(u64::MAX);
    let mut total: u64 = 0;
    let mut count: u64 = 0;
    for line in input.lines() {
        if line.is_empty() {
            continue;
        }
        let (key, rest) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let _key = key.trim();
        let rest = rest.trim();
        let value: u64 = rest.parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
    }
    if count > max_rows_u64 {
        return Err(SummaryError::TooMany);
    }
    let average = if count > 0 { total / count } else { 0 };
    Ok(Summary {
        count,
        total,
        average,
    })
}

pub fn render_summary(summary: Summary) -> String {
    format!(
        "count={} total={} average={}",
        summary.count, summary.total, summary.average
    )
}
