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
    let lines = input.lines();
    if lines.clone().next().is_none() {
        return Err(SummaryError::Empty);
    }
    let mut total = 0u64;
    let mut count = 0usize;
    for line in lines {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let (_name, value_str) = trimmed.split_once(',').ok_or(SummaryError::Invalid)?;
        let value = value_str
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    if count > max_rows {
        return Err(SummaryError::TooMany);
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

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
