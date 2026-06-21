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
    let mut total = 0u64;
    let mut count: u32 = 0;
    for line in input.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let (name, val_str) = trimmed.split_once(',').ok_or(SummaryError::Invalid)?;
        let _name = name.trim();
        let val_str = val_str.trim();
        let value: u64 = u64::try_from(val_str.parse::<u128>().map_err(|_| SummaryError::Invalid)?)
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        let next_count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
        count = next_count;
        if count as usize > max_rows {
            return Err(SummaryError::TooMany);
        }
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    let average = total
        .checked_div(count as u64)
        .ok_or(SummaryError::Overflow)?;
    Ok(Summary {
        count,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
