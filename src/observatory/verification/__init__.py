# FILE: src/observatory/verification/__init__.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Verification service package for multi-pass confidence labelling.
# PRD_REF: docs/PRD.md §24 v0.5
# WHY_REF: docs/why-graph.xml#MOD-VERIFY-SERVICE
# SCOPE: package exports for verification pass recording and confidence derivation
# INVARIANTS:
# - Importing this package never invokes real AgentRunner subprocesses.
# :END_MODULE_CONTRACT

from observatory.verification.service import (
    VerificationJobService,
    VerificationPass,
    confidence_from_pass_counts,
    confidence_from_verification_passes,
    verification_passes_for_evidence,
    verification_passes_for_items,
)

__all__ = [
    "VerificationJobService",
    "VerificationPass",
    "confidence_from_pass_counts",
    "confidence_from_verification_passes",
    "verification_passes_for_evidence",
    "verification_passes_for_items",
]
