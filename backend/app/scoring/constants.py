"""
Stable constants for reason codes and action keys.

These values are versioned and must remain stable for UI compatibility.
Version: v1
"""

# Reason codes - stable constants for point loss reasons
class ReasonCode:
    """Reason codes for point losses."""
    
    # Ownership dimension
    MISSING_OWNER = "missing_owner"
    MISSING_CONTACT = "missing_contact"
    
    # Documentation dimension
    MISSING_DESCRIPTION = "missing_description"
    INSUFFICIENT_COLUMN_DOCS = "insufficient_column_docs"
    
    # Schema hygiene dimension
    NAMING_CONVENTION_VIOLATIONS = "naming_convention_violations"
    HIGH_NULLABLE_RATIO = "high_nullable_ratio"
    LEGACY_COLUMNS_DETECTED = "legacy_columns_detected"
    
    # Data quality dimension
    MISSING_QUALITY_CHECKS = "missing_quality_checks"
    MISSING_SLA = "missing_sla"
    UNRESOLVED_FAILURES = "unresolved_failures"
    
    # Stability dimension
    BREAKING_CHANGES_DETECTED = "breaking_changes_detected"
    MISSING_CHANGELOG = "missing_changelog"
    BACKWARD_INCOMPATIBLE = "backward_incompatible"
    
    # Operational dimension
    MISSING_INTENDED_USE = "missing_intended_use"
    MISSING_LIMITATIONS = "missing_limitations"


# Action keys - stable constants for recommended actions
class ActionKey:
    """Action keys for recommended improvements."""
    
    # Ownership dimension
    ASSIGN_OWNER = "assign_owner"
    ADD_OWNER_CONTACT = "add_owner_contact"
    
    # Documentation dimension
    ADD_DESCRIPTION = "add_description"
    DOCUMENT_COLUMNS = "document_columns"
    
    # Schema hygiene dimension
    FIX_NAMING = "fix_naming"
    REDUCE_NULLABLE_COLUMNS = "reduce_nullable_columns"
    REMOVE_LEGACY_COLUMNS = "remove_legacy_columns"
    
    # Data quality dimension
    ADD_QUALITY_CHECKS = "add_quality_checks"
    DEFINE_SLA = "define_sla"
    RESOLVE_FAILURES = "resolve_failures"
    
    # Stability dimension
    PREVENT_BREAKING_CHANGES = "prevent_breaking_changes"
    ADD_CHANGELOG = "add_changelog"
    MAINTAIN_COMPATIBILITY = "maintain_compatibility"
    
    # Operational dimension
    DEFINE_INTENDED_USE = "define_intended_use"
    DOCUMENT_LIMITATIONS = "document_limitations"

