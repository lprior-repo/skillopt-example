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
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(SummaryError::Empty);
    }

    let mut total: u64 = 0;
    let mut count: usize = 0;

    for line in trimmed.lines() {
        if count >= max_rows {
            return Err(SummaryError::TooMany);
        }

        let (_, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let value: u64 = value_str
            .trim()
            .parse()
            .map_err(|_| SummaryError::Invalid)?;

        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }

    if count > max_rows {
        return Err(SummaryError::TooMany);
    }

    let count_u32 = u32::try_from(count).map_err(|_| SummaryError::Overflow)?;
    let count_u64 = u64::try_from(count).map_err(|_| SummaryError::Overflow)?;
    let average = if count > 0 {
        total.checked_div(count_u64).ok_or(SummaryError::Invalid)?
    } else {
        0
    };

    Ok(Summary {
        count: count_u32,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
