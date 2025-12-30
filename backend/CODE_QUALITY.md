# Code Quality Rules

This document outlines the code quality rules enforced in the Ondo codebase.

## Rules

### 1. Use Type Hints Everywhere in Python

✅ **Status: Enforced**

All Python functions must have complete type hints:
- Function parameters
- Return types
- Use `typing` module for complex types (List, Dict, Optional, etc.)

**Examples:**
```python
def score_dataset(metadata: Dict[str, Any]) -> ScoreResult:
    ...

def get_db() -> Generator[Session, None, None]:
    ...
```

### 2. Keep Functions Small; No Giant Controllers

✅ **Status: Enforced**

- API endpoints delegate to service functions
- Scoring logic split into dimension-specific modules
- Helper functions extracted for reusability
- No function exceeds ~100 lines

**Structure:**
- Controllers (`app/api/*.py`) - Handle HTTP requests/responses
- Services (`app/services/*.py`) - Business logic
- Scoring (`app/scoring/*.py`) - Pure scoring functions

### 3. Prefer Pure Functions for Scoring

✅ **Status: Enforced**

All scoring functions are pure:
- No side effects
- Deterministic (same input → same output)
- No database access
- No external API calls
- Easy to test

**Example:**
```python
def score_dataset(metadata: Dict) -> ScoreResult:
    """Pure function - no side effects."""
    ...
```

### 4. Every "Points Lost" Must Include Reason and Action

✅ **Status: Enforced**

Every point deduction must have:
- **Reason**: Human-readable explanation (e.g., "No owner assigned")
- **Action**: Remediation step with point gain (e.g., "Assign dataset owner (+10 points)")

**Pattern:**
```python
if not owner_name:
    reasons.append(
        Reason(
            dimension_key="ownership",
            reason_code="missing_owner",
            message="No owner assigned",  # Human-readable
            points_lost=10,
        )
    )
    actions.append(
        Action(
            action_key="assign_owner",
            title="Assign dataset owner",
            description="Assign a clear owner responsible for this dataset",
            points_gain=10,  # Matches points_lost
            dimension_key="ownership",
        )
    )
```

**Verification:**
- All dimension scorers checked
- Every `points_lost` has corresponding `Reason` and `Action`
- Actions include point gains matching the loss

### 5. Don't Invent Complex Integrations; Keep MVP Simple

✅ **Status: Enforced**

- Simple template-based AI suggestions (not LLM integration)
- Basic database queries (no complex ORM patterns)
- Straightforward API endpoints
- No unnecessary abstractions
- Focus on core functionality

## Code Review Checklist

When reviewing code, verify:

- [ ] All functions have type hints
- [ ] Functions are small and focused
- [ ] Scoring functions are pure (no side effects)
- [ ] Every point loss has reason + action
- [ ] No unnecessary complexity
- [ ] Tests cover scoring logic
- [ ] Error handling is appropriate

## Examples of Good Code

### ✅ Good: Type hints, small function, pure
```python
def score_ownership(
    metadata: Dict[str, Any],
) -> tuple[DimensionScore, List[Reason], List[Action]]:
    """Pure function with type hints."""
    ...
```

### ✅ Good: Reason + Action for point loss
```python
if not owner_name:
    reasons.append(Reason(..., message="No owner assigned", points_lost=10))
    actions.append(Action(..., points_gain=10))
```

### ❌ Bad: Missing type hints
```python
def score_ownership(metadata):  # Missing types
    ...
```

### ❌ Bad: Point loss without action
```python
if not owner_name:
    points_lost += 10  # No reason or action!
```

## Enforcement

- Type hints checked by mypy (can be added to CI)
- Code review ensures all rules are followed
- Tests verify scoring logic correctness

