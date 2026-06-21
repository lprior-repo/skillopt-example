#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SummaryError {
    Empty,
    Invalid,
    TooMany,
    Overflow,
    Allocation,
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
    let mut values: Vec<u64> = Vec::new();
    values
        .try_reserve(max_rows)
        .map_err(|_| SummaryError::Allocation)?;
    for line in input.lines() {
        let (_name, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let value = value_str
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        if values.len() >= max_rows {
            return Err(SummaryError::TooMany);
        }
        values.push(value);
    }
    if values.is_empty() {
        return Err(SummaryError::Empty);
    }
    let mut total: u64 = 0;
    let mut count: usize = 0;
    for &v in &values {
        total = total.checked_add(v).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }
    let count_u64 = u64::try_from(count).map_err(|_| SummaryError::Overflow)?;
    let average = total.checked_div(count_u64).ok_or(SummaryError::Invalid)?;
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
