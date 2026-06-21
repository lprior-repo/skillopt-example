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
        if trimmed.is_empty() {
            continue;
        }
        let (_key, val_str) = match trimmed.split_once(',') {
            Some((k, v)) => (k, v),
            None => return Err(SummaryError::Invalid),
        };
        let value = match val_str.trim().parse::<u64>() {
            Ok(v) => v,
            Err(_) => return Err(SummaryError::Invalid),
        };
        total = match total.checked_add(value) {
            Some(t) => t,
            None => return Err(SummaryError::Overflow),
        };
        count = match count.checked_add(1) {
            Some(c) => c,
            None => return Err(SummaryError::Overflow),
        };
    }

    if count == 0 {
        return Err(SummaryError::Empty);
    }

    if count > max_rows as u32 {
        return Err(SummaryError::TooMany);
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
