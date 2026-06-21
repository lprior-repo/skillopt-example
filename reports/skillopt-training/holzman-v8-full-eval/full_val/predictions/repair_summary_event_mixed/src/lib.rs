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

    if input.is_empty() {
        return Err(SummaryError::Empty);
    }

    for line in input.lines() {
        let parts: Vec<&str> = line.split(',').collect();
        if parts.len() < 2 {
            return Err(SummaryError::Invalid);
        }
        let value = parts[1]
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        match total.checked_add(value) {
            Some(v) => total = v,
            None => return Err(SummaryError::Overflow),
        }
        count += 1;
    }

    if count > max_rows {
        return Err(SummaryError::TooMany);
    }

    let count_u32 = count as u32;
    let average = total.checked_div(count_u32 as u64).unwrap_or(0);

    Ok(Summary {
        count: count_u32,
        total,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
