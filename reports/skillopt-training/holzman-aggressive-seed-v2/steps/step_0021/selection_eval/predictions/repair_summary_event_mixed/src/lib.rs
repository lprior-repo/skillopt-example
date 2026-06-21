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
        if line.trim().is_empty() {
            continue;
        }

        let (name, rest) = match line.split_once(',') {
            Some(parts) => parts,
            None => return Err(SummaryError::Invalid),
        };

        let name = name.trim();
        let value_str = rest.trim();

        if name.is_empty() || value_str.is_empty() {
            return Err(SummaryError::Invalid);
        }

        let value: u64 = match value_str.parse() {
            Ok(v) => v,
            Err(_) => return Err(SummaryError::Invalid),
        };

        total = match total.checked_add(value) {
            Some(t) => t,
            None => return Err(SummaryError::Overflow),
        };

        count += 1;

        if count > max_rows {
            return Err(SummaryError::TooMany);
        }
    }

    if count == 0 {
        return Err(SummaryError::Empty);
    }

    let average = total / count as u64;

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
