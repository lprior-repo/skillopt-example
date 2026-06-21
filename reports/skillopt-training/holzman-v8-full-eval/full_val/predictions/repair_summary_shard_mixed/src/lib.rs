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
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let (key, val_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let _key = key.trim();
        let val_str = val_str.trim();
        let value: u64 = val_str.parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::TooMany)?;
    }

    if count == 0 {
        return Err(SummaryError::Empty);
    }

    if count > max_rows {
        return Err(SummaryError::TooMany);
    }

    #[allow(clippy::as_conversions)]
    let count_u64 = count as u64;
    #[allow(clippy::arithmetic_side_effects)]
    let average = total / count_u64;

    let count_u32 = u32::try_from(count).map_err(|_| SummaryError::TooMany)?;

    Ok(Summary {
        count: count_u32,
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
