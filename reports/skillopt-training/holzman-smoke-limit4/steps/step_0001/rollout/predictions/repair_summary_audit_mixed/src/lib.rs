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
    if input.trim().is_empty() {
        return Err(SummaryError::Empty);
    }
    let mut total: u64 = 0;
    let mut count: u32 = 0;
    for line in input.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let Some((_, after_comma)) = trimmed.split_once(',') else {
            return Err(SummaryError::Invalid);
        };
        let value = after_comma
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
    }
    if count as usize > max_rows {
        return Err(SummaryError::TooMany);
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    let average = total / count as u64;
    Ok(Summary {
        count,
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
