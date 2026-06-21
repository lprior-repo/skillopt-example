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
        let parts: Vec<&str> = line.split(',').collect();
        let value = match parts.get(1) {
            Some(part) => part
                .trim()
                .parse::<u64>()
                .map_err(|_| SummaryError::Invalid)?,
            None => return Err(SummaryError::Invalid),
        };
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
    }

    if count == 0 {
        return Err(SummaryError::Empty);
    }

    if count > max_rows {
        return Err(SummaryError::TooMany);
    }

    let count_u32: u32 = count.try_into().map_err(|_| SummaryError::Overflow)?;
    let count_u64: u64 = count.try_into().map_err(|_| SummaryError::Overflow)?;
    let average = total.checked_div(count_u64).ok_or(SummaryError::Invalid)?;

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
