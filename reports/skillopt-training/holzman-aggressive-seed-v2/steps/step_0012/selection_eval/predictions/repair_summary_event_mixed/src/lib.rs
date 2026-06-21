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
    let mut count: usize = 0;
    for line in input.lines() {
        let (_, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let value: u64 = value_str
            .trim()
            .parse()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    if count > max_rows {
        return Err(SummaryError::TooMany);
    }
    let count_u32: u32 = u32::try_from(count).map_err(|_| SummaryError::Overflow)?;
    let average = total.checked_div(u64::from(count_u32)).unwrap_or(0);
    Ok(Summary {
        count: count_u32,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
