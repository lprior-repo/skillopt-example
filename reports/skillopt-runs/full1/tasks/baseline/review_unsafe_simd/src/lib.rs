#[cfg(target_arch = "x86_64")]
pub fn sum(input: &[f32]) -> f32 {
    unsafe {
        use std::arch::x86_64::*;
        let mut acc = _mm_setzero_ps();
        let mut i = 0;
        while i < input.len() {
            let ptr = input.as_ptr().add(i);
            acc = _mm_add_ps(acc, _mm_loadu_ps(ptr));
            i += 4;
        }
        let mut out = [0.0; 4];
        _mm_storeu_ps(out.as_mut_ptr(), acc);
        out.iter().sum()
    }
}
