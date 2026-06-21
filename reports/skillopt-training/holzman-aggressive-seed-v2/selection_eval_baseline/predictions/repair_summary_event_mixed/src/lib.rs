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
        let parts: Vec<&str> = line.split(',').map(|part| part.trim()).collect();
        if parts.len() < 2 || parts[1].is_empty() {
            return Err(SummaryError::Invalid);
        }
        let value = parts[1].parse::<u64>().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
        if count > max_rows {
            return Err(SummaryError::TooMany);
        }
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    let avg = total / count as u64;
    Ok(Summary {
        count: count as u32,
        total,
        average: avg,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
