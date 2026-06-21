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
    let mut count: u32 = 0;

    for line in input.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }

        let (_, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let value = value_str
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;

        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }

    if count == 0 {
        return Err(SummaryError::Empty);
    }

    let count_usize: usize = count.try_into().map_err(|_| SummaryError::Overflow)?;
    if count_usize > max_rows {
        return Err(SummaryError::TooMany);
    }

    let count_u64: u64 = count.into();
    let average = total.checked_div(count_u64).ok_or(SummaryError::Overflow)?;

    Ok(Summary {
        count,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
