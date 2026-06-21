#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SummaryError {
    Empty,
    Invalid,
    TooMany,
    Overflow,
}

impl std::fmt::Display for SummaryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SummaryError::Empty => write!(f, "empty input"),
            SummaryError::Invalid => write!(f, "invalid line"),
            SummaryError::TooMany => write!(f, "too many rows"),
            SummaryError::Overflow => write!(f, "overflow"),
        }
    }
}

impl std::error::Error for SummaryError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Summary {
    pub count: u32,
    pub total: u64,
    pub average: u64,
}

impl Summary {
    fn new(count: usize, total: u64) -> Result<Self, SummaryError> {
        let count_u32 = u32::try_from(count).map_err(|_| SummaryError::Overflow)?;
        let count_u64 = u64::try_from(count).map_err(|_| SummaryError::Overflow)?;
        let average = total.checked_div(count_u64).ok_or(SummaryError::Invalid)?;
        Ok(Self {
            count: count_u32,
            total,
            average,
        })
    }
}

pub fn summarize_metrics(input: &str, max_rows: usize) -> Result<Summary, SummaryError> {
    if input.is_empty() {
        return Err(SummaryError::Empty);
    }

    let mut total = 0u64;
    let mut count: usize = 0;

    for line in input.lines() {
        let (_name, value_str) = line.split_once(',').ok_or(SummaryError::Invalid)?;
        let value = value_str
            .trim()
            .parse::<u64>()
            .map_err(|_| SummaryError::Invalid)?;
        total = total.checked_add(value).ok_or(SummaryError::Overflow)?;
        count = count.checked_add(1).ok_or(SummaryError::Overflow)?;
        if count > max_rows {
            return Err(SummaryError::TooMany);
        }
    }

    Summary::new(count, total)
}

pub fn render_summary(summary: Summary) -> String {
    format!(
        "count={} total={} average={}",
        summary.count, summary.total, summary.average
    )
}
