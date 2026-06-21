use repair_metric_summary_layers::{render_summary, summarize_metrics, Summary, SummaryError};

#[test]
fn pure_summary_counts_total_and_average() {
    assert_eq!(
        summarize_metrics("cpu,10\nmem,5", 8),
        Ok(Summary { count: 2, total: 15, average: 7 })
    );
}

#[test]
fn rejects_empty_input() {
    assert_eq!(summarize_metrics("", 8), Err(SummaryError::Empty));
}

#[test]
fn rejects_invalid_line_without_panic() {
    assert_eq!(summarize_metrics("cpu=10", 8), Err(SummaryError::Invalid));
}

#[test]
fn rejects_too_many_rows_before_rendering() {
    assert_eq!(summarize_metrics("a,1\nb,2", 1), Err(SummaryError::TooMany));
}

#[test]
fn detects_total_overflow() {
    assert_eq!(
        summarize_metrics("a,18446744073709551615\nb,1", 4),
        Err(SummaryError::Overflow)
    );
}

#[test]
fn render_summary_is_separate_from_calculation() {
    assert_eq!(
        render_summary(Summary { count: 2, total: 15, average: 7 }),
        "count=2 total=15 average=7"
    );
}
