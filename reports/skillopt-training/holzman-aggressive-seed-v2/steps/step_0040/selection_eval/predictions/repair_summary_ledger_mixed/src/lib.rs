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
    let mut count: u32 = 0;
    for line in input.lines() {
        let trimmed = line.trim();
        let (_, rest) = trimmed.split_once(',').ok_or(SummaryError::Invalid)?;
        let value_str = rest.trim();
        let value: u64 = value_str.parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    if count as usize > max_rows {
        return Err(SummaryError::TooMany);
    }
    let average = total
        .checked_div(u64::from(count))
        .ok_or(SummaryError::Overflow)?;
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
