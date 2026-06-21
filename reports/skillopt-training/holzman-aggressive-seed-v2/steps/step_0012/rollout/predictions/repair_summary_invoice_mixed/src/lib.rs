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
    let mut count: u32 = 0;

    for line in input.lines() {
        let (key, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let _key = key.trim();
        let value_str = value_str.trim();
        let value: u64 = value_str.parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
        if count > max_rows as u32 {
            return Err(SummaryError::TooMany);
        }
    }

    if count == 0 {
        return Err(SummaryError::Empty);
    }

    let average = total.checked_div(count as u64).unwrap_or(0);

    Ok(Summary {
        count,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
