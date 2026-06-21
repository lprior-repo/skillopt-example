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
    if input.is_empty() || input.lines().all(|l| l.trim().is_empty()) {
        return Err(SummaryError::Empty);
    }
    let mut total: u64 = 0;
    let mut count: u64 = 0;
    for line in input.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let (_, rest) = trimmed.split_once(',').ok_or(SummaryError::Invalid)?;
        let value = rest
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }
    if count > max_rows as u64 {
        return Err(SummaryError::TooMany);
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    let count_u32: u32 = count.try_into().map_err(|_| SummaryError::Overflow)?;
    let average = total.checked_div(count).ok_or(SummaryError::Invalid)?;
    Ok(Summary {
        count: count_u32,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
