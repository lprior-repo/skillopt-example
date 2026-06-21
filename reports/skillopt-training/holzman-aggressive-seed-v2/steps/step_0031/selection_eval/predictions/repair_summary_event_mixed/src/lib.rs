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
    let mut lines = input.lines();
    let first = lines.next().ok_or(SummaryError::Empty)?;
    if !first.contains(',') {
        return Err(SummaryError::Invalid);
    }
    let mut total: u64 = 0;
    let mut count: usize = 0;
    let iter = std::iter::once(first).chain(lines);
    for line in iter {
        let (_, rest) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let value: u64 = rest.trim().parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }
    let count_u32: u32 = u32::try_from(count).map_err(|_| SummaryError::Overflow)?;
    if count > max_rows {
        return Err(SummaryError::TooMany);
    }
    let average = total
        .checked_div(count as u64)
        .ok_or(SummaryError::Invalid)?;
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
