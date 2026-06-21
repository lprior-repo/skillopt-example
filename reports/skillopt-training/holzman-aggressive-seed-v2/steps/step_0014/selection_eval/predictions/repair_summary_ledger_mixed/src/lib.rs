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
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let (key, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        if key.trim().is_empty() || value_str.trim().is_empty() {
            return Err(SummaryError::Invalid);
        }
        let value: u64 = value_str
            .trim()
            .parse()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }

    if count == 0 {
        return Err(SummaryError::Empty);
    }
    if count > u64::try_from(max_rows).unwrap_or(u64::MAX) {
        return Err(SummaryError::TooMany);
    }

    let average = total.checked_div(count).unwrap_or(0);
    let count_u32 = u32::try_from(count).map_err(|_| SummaryError::Overflow)?;

    Ok(Summary {
        count: count_u32,
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
