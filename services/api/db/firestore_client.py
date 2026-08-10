"""Firestore state store boundary — Phase 2.

This file defines the interface for the Firestore implementation.
Phase 1 uses LocalStateStore exclusively.

Authentication: Application Default Credentials (ADC) only.
No service account JSON key files.
"""
from __future__ import annotations


class FirestoreStateStore:
    """Phase 2 Firestore implementation.

    Activated when GOOGLE_CLOUD_PROJECT is set in environment.
    Uses Application Default Credentials (ADC) — no key files required.

    To configure ADC for local development:
        gcloud auth application-default login

    For Cloud Run: attach a service account with least-privilege IAM roles:
        roles/datastore.user

    DO NOT create or use long-lived service account JSON key files.
    """

    def __init__(self) -> None:
        raise NotImplementedError(
            "FirestoreStateStore is a Phase 2 component.\n"
            "Phase 1 uses LocalStateStore.\n"
            "To enable Firestore: set GOOGLE_CLOUD_PROJECT and configure ADC.\n"
            "See docs/adr/001-event-driven-state.md"
        )
