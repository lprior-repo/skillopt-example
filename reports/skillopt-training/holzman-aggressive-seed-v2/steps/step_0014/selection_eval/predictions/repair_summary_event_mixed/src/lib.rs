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

    let max_rows = u32::try_from(max_rows).map_err(|_| SummaryError::TooMany)?;
    let mut total = 0u64;
    let mut count: u32 = 0;

    for line in input.lines() {
        let Some((_, rest)) = line.split_once(',') else {
            return Err(SummaryError::Invalid);
        };
        let value = rest
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::TooMany)?;
        if count > max_rows {
            return Err(SummaryError::TooMany);
        }
    }

    let average = total.checked_div(u64::from(count)).unwrap_or(0);
    Ok(Summary {
        count,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
