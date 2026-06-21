use std::fs;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SummaryError {
    Io,
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
    let mut labels: Vec<String> = Vec::new();

    for line in input.lines() {
        if line.is_empty() {
            continue;
        }
        let (label, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let value: u64 = value_str
            .trim()
            .parse()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count += 1;
        labels.push(label.trim().to_string());
    }

    if count > max_rows {
        return Err(SummaryError::TooMany);
    }

    let count_u32 = count as u32;
    let average = total
        .checked_div(count_u32 as u64)
        .ok_or(SummaryError::Overflow)?;

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

pub fn summarize_file(path: &str, max_rows: usize) -> Result<String, SummaryError> {
    let text = fs::read_to_string(path).map_err(|_| SummaryError::Io)?;
    let summary = summarize_metrics(&text, max_rows)?;
    Ok(render_summary(summary))
}
