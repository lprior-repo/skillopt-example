/// Budget lifecycle typestates. Illegal state transitions are unrepresentable.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BudgetState {
    /// Budget has been created but not yet validated.
    Created { id: String },
    /// Budget has been validated. Ready to be sent.
    Validated { id: String },
    /// Budget has been sent. Contains the validation flag and timestamp.
    Sent { id: String, sent_at_epoch_ms: u64 },
}

impl BudgetState {
    /// Create a new budget in the `Created` state.
    pub fn created(id: String) -> Self {
        Self::Created { id }
    }

    /// Transition from `Created` to `Validated`.
    ///
    /// Returns `InvalidTransition` if the budget is not in the `Created` state.
    pub fn validate(self) -> Result<Self, InvalidTransition> {
        match self {
            Self::Created { id } => Ok(Self::Validated { id }),
            other => Err(InvalidTransition {
                from: state_label(&other),
                to: "Validated",
            }),
        }
    }

    /// Transition from `Validated` to `Sent`.
    ///
    /// Requires the budget to be in the `Validated` state. Takes the
    /// submission timestamp and returns the `Sent` state.
    pub fn mark_sent(self, sent_at_epoch_ms: u64) -> Result<Self, InvalidTransition> {
        match self {
            Self::Validated { id } => Ok(Self::Sent {
                id,
                sent_at_epoch_ms,
            }),
            other => Err(InvalidTransition {
                from: state_label(&other),
                to: "Sent",
            }),
        }
    }

    /// Returns `true` if this budget is in the `Sent` state.
    pub fn is_sent(&self) -> bool {
        matches!(self, Self::Sent { .. })
    }

    /// Returns the epoch-millisecond timestamp if the budget has been sent.
    pub fn sent_at_epoch_ms(&self) -> Option<u64> {
        match self {
            Self::Sent {
                sent_at_epoch_ms, ..
            } => Some(*sent_at_epoch_ms),
            _ => None,
        }
    }

    /// Returns the budget id, regardless of state.
    pub fn id(&self) -> &str {
        match self {
            Self::Created { id } | Self::Validated { id } | Self::Sent { id, .. } => id.as_str(),
        }
    }
}

/// Error returned when a state transition is attempted from an invalid state.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InvalidTransition {
    from: String,
    to: &'static str,
}

impl std::fmt::Display for InvalidTransition {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "cannot transition from {} to {}", self.from, self.to)
    }
}

impl std::error::Error for InvalidTransition {}

/// Helper to produce a label string for an `InvalidTransition` source state.
fn state_label(state: &BudgetState) -> String {
    match state {
        BudgetState::Created { .. } => "Created".to_string(),
        BudgetState::Validated { .. } => "Validated".to_string(),
        BudgetState::Sent { .. } => "Sent".to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn created_to_validated() {
        let budget = BudgetState::created("b-42".to_string());
        let validated = budget.validate().unwrap();
        assert!(matches!(validated, BudgetState::Validated { .. }));
        assert_eq!(validated.id(), "b-42");
        assert!(!validated.is_sent());
        assert_eq!(validated.sent_at_epoch_ms(), None);
    }

    #[test]
    fn validated_to_sent() {
        let budget = BudgetState::created("b-42".to_string()).validate().unwrap();
        let sent = budget.mark_sent(1_700_000_000).unwrap();
        assert!(matches!(sent, BudgetState::Sent { .. }));
        assert_eq!(sent.id(), "b-42");
        assert!(sent.is_sent());
        assert_eq!(sent.sent_at_epoch_ms(), Some(1_700_000_000));
    }

    #[test]
    fn cannot_mark_sent_from_created() {
        let budget = BudgetState::created("b-42".to_string());
        let result = budget.mark_sent(1_700_000_000);
        assert!(result.is_err());
        let err = result.unwrap_err();
        assert_eq!(err.from, "Created");
        assert_eq!(err.to, "Sent");
    }

    #[test]
    fn cannot_validate_sent() {
        let budget = BudgetState::created("b-42".to_string())
            .validate()
            .unwrap()
            .mark_sent(1_700_000_000)
            .unwrap();
        let result = budget.validate();
        assert!(result.is_err());
    }

    #[test]
    fn cannot_mark_sent_twice() {
        let budget = BudgetState::created("b-42".to_string())
            .validate()
            .unwrap()
            .mark_sent(1_700_000_000)
            .unwrap();
        let result = budget.mark_sent(1_700_000_001);
        assert!(result.is_err());
    }

    #[test]
    fn is_sent_returns_false_for_non_sent() {
        let created = BudgetState::created("b-42".to_string());
        assert!(!created.is_sent());

        let validated = created.validate().unwrap();
        assert!(!validated.is_sent());
    }

    #[test]
    fn is_sent_returns_true_for_sent() {
        let budget = BudgetState::created("b-42".to_string())
            .validate()
            .unwrap()
            .mark_sent(1_700_000_000)
            .unwrap();
        assert!(budget.is_sent());
    }

    #[test]
    fn sent_at_epoch_ms_none_before_sent() {
        let created = BudgetState::created("b-42".to_string());
        assert_eq!(created.sent_at_epoch_ms(), None);

        let validated = created.validate().unwrap();
        assert_eq!(validated.sent_at_epoch_ms(), None);
    }
}
