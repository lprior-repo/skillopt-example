use std::fs;

#[derive(Debug, Clone)]
pub struct Reading {
    pub sensor: String,
    pub value: u16,
    pub flags: Vec<String>,
}

pub fn load_readings(path: &str) -> Vec<Reading> {
    let text = fs::read_to_string(path).unwrap();
    text.lines()
        .map(|line| {
            let parts: Vec<String> = line.split(',').map(|part| part.trim().to_string()).collect();
            let value = parts[1].parse::<u32>().unwrap() as u16;
            println!("loaded {}", parts[0]);
            Reading {
                sensor: parts[0].clone(),
                value,
                flags: parts[2].split('|').map(|flag| flag.to_string()).collect(),
            }
        })
        .collect()
}
