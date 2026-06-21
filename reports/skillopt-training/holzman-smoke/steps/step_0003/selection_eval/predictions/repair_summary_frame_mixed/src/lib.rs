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
    if input.trim().is_empty() {
        return Err(SummaryError::Empty);
    }
    let mut total: u64 = 0;
    let mut count: u64 = 0;
    for line in input.lines() {
        let trimmed = line.trim();
        let (key, value_str) = trimmed.split_once(',').ok_or(SummaryError::Invalid)?;
        let _key = key.trim();
        let value = value_str
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }
    if count > max_rows as u64 {
        return Err(SummaryError::TooMany);
    }
    let average = total / count;
    Ok(Summary {
        count: count as u32,
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
