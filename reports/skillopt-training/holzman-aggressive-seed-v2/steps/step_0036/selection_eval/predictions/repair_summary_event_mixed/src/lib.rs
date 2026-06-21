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
    let mut count: u32 = 0;

    for line in input.lines() {
        let (_, rest) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let value: u64 = rest.trim().parse().map_err(|_| SummaryError::Invalid)?;

        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        let next = u32::try_from(count).ok().and_then(|c| c.checked_add(1));
        count = next.ok_or(SummaryError::Overflow)?;
    }

    if count as usize > max_rows {
        return Err(SummaryError::TooMany);
    }

    let average = total
        .checked_div(count as u64)
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
