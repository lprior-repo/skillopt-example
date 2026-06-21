pub fn parse_scores(input: &str) -> Vec<u32> {
    input
        .lines()
        .map(|line| line.trim().parse::<u32>().unwrap())
        .collect()
}
