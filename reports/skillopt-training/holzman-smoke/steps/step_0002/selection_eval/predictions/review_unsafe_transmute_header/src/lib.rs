pub fn read_len(input: &[u8]) -> u32 {
    unsafe { std::mem::transmute::<[u8; 4], u32>([input[0], input[1], input[2], input[3]]) }
}
