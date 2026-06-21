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
    let mut count: u64 = 0;

    for line in input.lines() {
        let parts: Vec<&str> = line.split(',').collect();
        if parts.len() < 2 {
            return Err(SummaryError::Invalid);
        }
        let value_str = parts[1].trim();
        let value: u64 = value_str.parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
    }

    if count == 0 {
        return Err(SummaryError::Empty);
    }
    if count > max_rows as u64 {
        return Err(SummaryError::TooMany);
    }

    let avg = total / count;
    Ok(Summary {
        count: count as u32,
        total,
        average: avg,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
