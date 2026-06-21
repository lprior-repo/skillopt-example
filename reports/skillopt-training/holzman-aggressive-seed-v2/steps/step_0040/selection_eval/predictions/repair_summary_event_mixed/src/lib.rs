use std::fmt::Write;

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
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let (key, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let _key = key.trim();
        let value_str = value_str.trim();
        let value: u64 = value_str.parse().map_err(|_| SummaryError::Invalid)?;

        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
    }

    if count > max_rows as u32 {
        return Err(SummaryError::TooMany);
    }

    let average = total
        .checked_div(u64::from(count))
        .ok_or(SummaryError::Empty)?;

    Ok(Summary {
        count,
        total,
        average,
    })
}

pub fn render_summary(summary: Summary) -> String {
    let mut buf = String::new();
    let _ = write!(
        buf,
        "count={} total={} average={}",
        summary.count, summary.total, summary.average
    );
    buf
}
