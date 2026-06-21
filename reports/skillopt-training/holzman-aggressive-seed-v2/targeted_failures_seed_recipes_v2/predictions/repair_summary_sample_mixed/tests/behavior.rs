use repair_summary_sample_mixed::{render_summary, summarize_metrics, Summary, SummaryError};

#[test]
fn summarizes() {
    assert_eq!(
        summarize_metrics("a,10\nb,5", 8),
        Ok(Summary {
            count: 2,
            total: 15,
            average: 7
        })
    );
}
#[test]
fn renders() {
    assert_eq!(
        render_summary(Summary {
            count: 2,
            total: 15,
            average: 7
        }),
        "count=2 total=15 average=7"
    );
}
#[test]
fn rejects_empty() {
    assert_eq!(summarize_metrics("", 8), Err(SummaryError::Empty));
}
#[test]
fn rejects_invalid() {
    assert_eq!(summarize_metrics("bad", 8), Err(SummaryError::Invalid));
}
#[test]
fn rejects_too_many() {
    assert_eq!(summarize_metrics("a,1\nb,2", 1), Err(SummaryError::TooMany));
}
#[test]
fn detects_overflow() {
    assert_eq!(
        summarize_metrics("a,18446744073709551615\nb,1", 4),
        Err(SummaryError::Overflow)
    );
}
