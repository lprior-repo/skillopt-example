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
    if input.lines().next().is_none() {
        return Err(SummaryError::Empty);
    }
    let mut total = 0u64;
    let mut count = 0usize;
    for line in input.lines() {
        let parts: Vec<&str> = line.split(',').collect();
        let value = parts.get(1).ok_or(SummaryError::Invalid)?;
        let value = value
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
    }
    if count > max_rows {
        return Err(SummaryError::TooMany);
    }
    let average = total.checked_div(count as u64).unwrap_or(0);
    Ok(Summary {
        count: u32::try_from(count).unwrap_or(u32::MAX),
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
