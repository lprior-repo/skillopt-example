use std::collections::HashMap;

pub fn route(event: serde_json::Value, rules: HashMap<String, serde_json::Value>) -> Option<String> {
    let name = event.get("name")?.as_str()?.to_string();
    for (key, value) in rules {
        if value.get("enabled")?.as_bool()? && key == name {
            return Some(format!("route:{key}"));
        }
    }
    None
}
