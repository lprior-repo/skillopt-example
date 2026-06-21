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
    let mut lines: Vec<&str> = Vec::new();
    lines
        .try_reserve(max_rows)
        .map_err(|_| SummaryError::Overflow)?;
    let mut total: u64 = 0;
    for line in input.lines() {
        let (_name, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let value = value_str
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        lines.push(line);
    }
    let count = lines.len();
    if count == 0 {
        return Err(SummaryError::Empty);
    }
    if count > max_rows {
        return Err(SummaryError::TooMany);
    }
    let total_u64 = total;
    let count_u32: u32 = count.try_into().map_err(|_| SummaryError::Overflow)?;
    let average = total_u64
        .checked_div(u64::from(count_u32))
        .ok_or(SummaryError::Overflow)?;
    Ok(Summary {
        count: count_u32,
        total: total_u64,
        average,
    })
}

pub fn render_summary(s: Summary) -> String {
    format!("count={} total={} average={}", s.count, s.total, s.average)
}
