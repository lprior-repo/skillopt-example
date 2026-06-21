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
        let parts: Vec<&str> = line.split(',').collect();
        let value = match parts.get(1) {
            Some(v) => v.trim().parse::<u64>().map_err(|_| SummaryError::Invalid)?,
            None => return Err(SummaryError::Invalid),
        };
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }

    if count > max_rows.try_into().unwrap_or(u32::MAX) {
        return Err(SummaryError::TooMany);
    }

    #[allow(clippy::arithmetic_side_effects)]
    let average = total.saturating_div(u64::from(count));

    Ok(Summary {
        count,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
