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
    let mut count: usize = 0;
    for line in input.lines() {
        let parts: Vec<&str> = line.split(',').collect();
        if parts.len() != 2 {
            return Err(SummaryError::Invalid);
        }
        let value = parts[1]
            .trim()
            .parse::<u64>()
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
    let average = total / count as u64;
    Ok(Summary {
        count: count as u32,
        total,
        average,
    })
}

pub fn render_summary(summary: Summary) -> String {
    format!(
        "count={} total={} average={}",
        summary.count, summary.total, summary.average
    )
}
