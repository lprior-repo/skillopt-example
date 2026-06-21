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
    let mut total = 0u64;
    let mut count = 0usize;
    for line in input.lines() {
        let parts: Vec<&str> = line.split(',').map(|part| part.trim()).collect();
        if parts.len() < 2 {
            return Err(SummaryError::Invalid);
        }
        let value = match parts[1].parse::<u64>() {
            Ok(v) => v,
            Err(_) => return Err(SummaryError::Invalid),
        };
        total = match total.checked_add(value) {
            Some(t) => t,
            None => return Err(SummaryError::Overflow),
        };
        count += 1;
    }
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    if count > max_rows {
        return Err(SummaryError::TooMany);
    }
    let average = match total.checked_div(count as u64) {
        Some(a) => a,
        None => return Err(SummaryError::Overflow),
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
