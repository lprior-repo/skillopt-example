use std::fs;

pub struct Record {
    pub name: String,
    pub value: u16,
}

pub fn load_audits(path: &str) -> Vec<Record> {
    let text = fs::read_to_string(path).unwrap();
    text.lines()
        .map(|line| {
            let parts: Vec<String> = line
                .split(',')
                .map(|part| part.trim().to_string())
                .collect();
            println!("loaded {}", parts[0]);
            Record {
                name: parts[0].clone(),
                value: parts[1].parse::<u32>().unwrap() as u16,
            }
        })
        .collect()
}
