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
    let mut total = 0u64;
    let mut count = 0usize;
    for line in input.lines() {
        let (name, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let _name = name.trim();
        let value_str = value_str.trim();
        let value = value_str
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
        if count > max_rows {
            return Err(SummaryError::TooMany);
        }
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
    }
    let count_u32 = u32::try_from(count).map_err(|_| SummaryError::Overflow)?;
    let count_u64 = u64::try_from(count).map_err(|_| SummaryError::Overflow)?;
    let average = total.checked_div(count_u64).ok_or(SummaryError::Invalid)?;
    Ok(Summary {
        count: count_u32,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
