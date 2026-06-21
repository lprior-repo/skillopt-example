pub struct PacketWorkflow {
    pub id: String,
    pub status: String,
    pub is_validated: bool,
    pub is_sent: bool,
    pub sent_at_epoch_ms: Option<u64>,
}

pub fn mark_sent(mut item: PacketWorkflow) -> PacketWorkflow {
    item.status = "sent".to_string();
    item.is_sent = true;
    item
}
