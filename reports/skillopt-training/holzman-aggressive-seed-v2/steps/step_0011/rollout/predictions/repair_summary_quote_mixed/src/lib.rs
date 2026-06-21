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
    let mut total: u64 = 0;
    let mut count: usize = 0;
    for line in input.lines() {
        let (label, rest) = match line.split_once(',') {
            Some((l, r)) => (l.trim(), r.trim()),
            None => return Err(SummaryError::Invalid),
        };
        if label.is_empty() {
            return Err(SummaryError::Invalid);
        }
        let value: u64 = match rest.parse() {
            Ok(v) => v,
            Err(_) => return Err(SummaryError::Invalid),
        };
        total = match total.checked_add(value) {
            Some(t) => t,
            None => return Err(SummaryError::Overflow),
        };
        count += 1;
    }
    if count > max_rows {
        return Err(SummaryError::TooMany);
    }
    let average = match total.checked_div(count as u64) {
        Some(a) => a,
        None => return Err(SummaryError::Empty),
    };
    Ok(Summary {
        count: count as u32,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
