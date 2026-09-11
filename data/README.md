# Data Directory Documentation

## Overview

This dataset is synthetically authored specifically for this project to avoid using private, personal, or proprietary email data.

## Why Synthetic Professional Email Data?

Professional email communication follows structured, recurring intent patterns across business domains (such as scheduling, approvals, customer support, project updates, and technical inquiries). Using synthetically generated professional emails allows us to:
1. Ensure full compliance with privacy and data protection standards (no PII or confidential company data).
2. Control coverage across diverse communication intents, tones, urgency levels, and request types.
3. Provide a clean, grounded benchmark for vector retrieval and LLM response generation.

## Categories Covered

The dataset includes over 600 email/reply pairs distributed across 15 representative categories:

1. **Meeting**: Aligning on agendas, setting sync calls, and confirming attendance.
2. **Scheduling**: Managing reschedules, calendar availability, and interview loops.
3. **Customer Support**: Handling order inquiries, refund requests, and account unlocks.
4. **Internship/Job**: Managing job applications, interview follow-ups, and offer acceptances.
5. **Leave Request**: Formal requests and approvals for annual, sick, or emergency leave.
6. **Project Update**: Milestone reports, blocker alerts, and release readiness notifications.
7. **Document Request**: Sharing and requesting contracts, specs, and financial reports.
8. **Follow-up**: Tracking pending proposals, tickets, and decisions.
9. **Payment/Billing**: Processing invoices, billing inquiries, and wire confirmations.
10. **Technical Issue**: Reporting and resolving outages, SSH timeouts, and pipeline errors.
11. **Apology**: Professional apologies for missed calls, draft oversights, or delays.
12. **Confirmation**: Confirming document receipt, summit attendance, or payment settlements.
13. **Invitation**: Event invitations, speaker invites, and beta testing requests.
14. **Information Request**: Inquiring about service tiers, SLAs, and technical specs.
15. **Professional Networking**: Reaching out for intro calls, conference connections, and alumni networking.

## Dataset Structure

- `raw/emails.json`: Generated raw dataset containing at least 600 items with fields (`id`, `category`, `incoming_email`, `reference_reply`).
- `processed/train.json`: 70% split reserved for retrieval indexing and grounding examples.
- `processed/validation.json`: 15% split for prompt tuning and hyperparameter evaluation.
- `processed/test.json`: 15% split held out for final evaluation. (Note: Test examples are strictly excluded from vector indices to prevent data leakage).
