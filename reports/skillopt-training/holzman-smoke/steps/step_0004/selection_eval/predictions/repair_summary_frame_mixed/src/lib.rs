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
    let mut count: usize = 0;

    for line in input.lines() {
        let comma_pos = line.split_once(',');
        match comma_pos {
            Some((_, value_str)) => {
                let value = value_str
                    .trim()
                    .parse::<u64>()
                    .map_err(|_| SummaryError::Invalid)?;
                total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
                count += 1;
            }
            None => return Err(SummaryError::Invalid),
        }
    }

    if count > max_rows {
        return Err(SummaryError::TooMany);
    }

    let average = if count > 0 { total / count as u64 } else { 0 };

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
