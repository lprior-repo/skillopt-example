#![allow(clippy::arithmetic_side_effects)]

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

impl Summary {
    pub fn from_fields(count: u32, total: u64, average: u64) -> Result<Summary, SummaryError> {
        if count == 0 {
            return Err(SummaryError::Invalid);
        }
        if average != total / u64::from(count) {
            return Err(SummaryError::Invalid);
        }
        Ok(Summary {
            count,
            total,
            average,
        })
    }
}

pub fn summarize_metrics(input: &str, max_rows: usize) -> Result<Summary, SummaryError> {
    if input.is_empty() {
        return Err(SummaryError::Empty);
    }

    let mut total: u64 = 0;
    let mut count: usize = 0;

    for line in input.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let (_, rest) = trimmed.split_once(',').ok_or(SummaryError::Invalid)?;
        let value_str = rest.trim();
        let value: u64 = value_str.parse().map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
        if count > max_rows {
            return Err(SummaryError::TooMany);
        }
    }

    if count == 0 {
        return Err(SummaryError::Empty);
    }

    #[allow(clippy::as_conversions)]
    let average_u64 = total
        .checked_div(count as u64)
        .ok_or(SummaryError::Invalid)?;
    let count_u32 = u32::try_from(count).map_err(|_| SummaryError::Overflow)?;

    Summary::from_fields(count_u32, total, average_u64)
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
