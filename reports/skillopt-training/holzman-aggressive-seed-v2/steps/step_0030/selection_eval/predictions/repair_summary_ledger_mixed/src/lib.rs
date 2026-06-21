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
        let trimmed = line.trim();
        let (_, value_str) = trimmed.split_once(',').ok_or(SummaryError::Invalid)?;
        let value = value_str
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::TooMany)?;
    }

    if count == 0 {
        return Err(SummaryError::Empty);
    }

    let max_rows_limit = match u32::try_from(max_rows) {
        Ok(v) => v,
        Err(_) => u32::MAX,
    };
    if count > max_rows_limit {
        return Err(SummaryError::TooMany);
    }

    let average = match total.checked_div(count as u64) {
        Some(average) => average,
        None => 0,
    };

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
