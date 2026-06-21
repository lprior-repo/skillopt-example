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
    let mut count: u64 = 0;
    for line in input.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let (_name, val_str) = trimmed.split_once(',').ok_or(SummaryError::Invalid)?;
        let value: u64 = val_str.trim().parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    if count > max_rows as u64 {
        return Err(SummaryError::TooMany);
    }
    let average = total / count;
    Ok(Summary {
        count: u32::try_from(count).map_err(|_| SummaryError::Invalid)?,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
