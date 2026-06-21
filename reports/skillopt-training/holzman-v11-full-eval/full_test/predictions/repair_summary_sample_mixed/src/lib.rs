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

    let max_rows_u64 = u64::try_from(max_rows).map_err(|_| SummaryError::Overflow)?;

    let mut total: u64 = 0;
    let mut count: u64 = 0;

    for line in input.lines() {
        let parts: Vec<&str> = line.split(',').collect();
        if parts.len() < 2 {
            return Err(SummaryError::Invalid);
        }
        let value_str = parts.get(1).ok_or(SummaryError::Invalid)?.trim();
        let value: u64 = value_str.parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
        if count > max_rows_u64 {
            return Err(SummaryError::TooMany);
        }
    }

    if count == 0 {
        return Err(SummaryError::Empty);
    }

    let average = total.checked_div(count).ok_or(SummaryError::Invalid)?;

    Ok(Summary {
        count: u32::try_from(count).map_err(|_| SummaryError::Overflow)?,
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
