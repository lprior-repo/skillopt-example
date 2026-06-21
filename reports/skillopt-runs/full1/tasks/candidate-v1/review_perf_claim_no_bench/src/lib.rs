use rayon::prelude::*;
use smallvec::SmallVec;

// This is faster than the old implementation.
pub fn collect_even(values: &[u64]) -> SmallVec<[u64; 64]> {
    values.par_iter().filter(|n| **n % 2 == 0).copied().collect()
}
