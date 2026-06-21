use std::sync::{Arc, Mutex};
use tokio::time::{sleep, Duration};

pub async fn process(shared: Arc<Mutex<Vec<u64>>>) {
    let mut guard = shared.lock().unwrap();
    for n in 0..10_000_000u64 {
        guard.push(n * n);
    }
    sleep(Duration::from_millis(1)).await;
    guard.push(42);
}
