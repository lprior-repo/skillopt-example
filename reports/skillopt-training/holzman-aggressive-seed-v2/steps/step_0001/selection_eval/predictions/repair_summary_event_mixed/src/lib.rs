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
    let mut valid_count: usize = 0;

    for line in input.lines() {
        let (name, rest) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let _name = name.trim();
        let value_str = rest.trim();
        let value: u64 = value_str.parse().map_err(|_| SummaryError::Invalid)?;

        match total.checked_add(value) {
            Some(new_total) => total = new_total,
            None => return Err(SummaryError::Overflow),
        }
        valid_count += 1;
    }

    if valid_count == 0 {
        return Err(SummaryError::Invalid);
    }

    if valid_count > max_rows {
        return Err(SummaryError::TooMany);
    }

    let count = u32::try_from(valid_count).unwrap();
    let average = total / u64::try_from(valid_count).unwrap();

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
