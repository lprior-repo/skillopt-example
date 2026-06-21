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

    let mut total: Option<u64> = None;
    let mut count: u32 = 0;

    for line in input.lines() {
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
        if count as usize > max_rows {
            return Err(SummaryError::TooMany);
        }

        let (_, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let value: u64 = value_str
            .trim()
            .parse()
            .map_err(|_| SummaryError::Invalid)?;

        total = Some(
            total
                .map(|t| t.checked_add(value).ok_or(SummaryError::Overflow))
                .unwrap_or(Ok(value))?,
        );
    }

    let total = total.ok_or(SummaryError::Empty)?;
    let average = total.checked_div(u64::from(count)).unwrap_or(0);

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
