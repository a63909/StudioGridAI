# StudioGrid AI project chronology

Verified on 2026-08-21 for the All Things Agentic Hackathon submission package.

## Contest window

- Submission period opens: **August 3, 2026 at 9:00 AM Pacific Time**.
- Submission period closes: **August 31, 2026 at 5:00 PM Pacific Time**.
- Binding source: <https://allthingsagentichackathon.devpost.com/rules>.

## Git evidence

The earliest reachable StudioGrid commit is:

```text
6d2adcc4a0ec3194a1a0b4738e0f5b78ff694374
AuthorDate: 2026-08-11T02:40:55+03:00
CommitDate: 2026-08-11T02:40:55+03:00
Subject: STUDIOGRID_AI_FOUNDATION_MVP_1
```

The following read-only check returned no commits:

```text
git log --all --reflog --before="2026-08-03T09:00:00-07:00" \
  --date=iso-strict --format="%H %aI %cI %s"

<no output>
```

Accordingly, **no pre-contest StudioGrid Git commit evidence was found in this repository**. `git fsck --full --no-reflogs --unreachable` reported three unreachable blobs but no unreachable commits or trees. A standalone Git blob has no commit timestamp and is not evidence of work before the contest.

## Generated-document date correction

The first committed version of `docs/IBM_BOB_DEVELOPMENT_LOG.md` is in the root commit above. That version contained six generated metadata lines reading `**Date:** 2025`. Several Phase 1 ADRs and the generated planning artifact repeated the same year, and the MIT license header also said 2025.

Those strings are **generated-document claims**, not independent proof of a 2025 StudioGrid artifact. They conflict with the repository's Git chronology. This submission milestone therefore corrects only demonstrably erroneous project-document metadata to the truthful non-day-specific wording **August 2026**, or to **2026** for the copyright year. Git history preserves the original versions and makes the correction auditable.

## Dates deliberately not changed

The fictional `LAST LIGHT` production package intentionally uses 2025 dates as synthetic story data. Test fixtures and local fallback values tied to that fictional shoot day also use 2025. Those values do not claim that StudioGrid itself existed in 2025 and remain unchanged.

## Evidence classification

| Evidence | Classification | What it proves |
|---|---|---|
| Reachable commits with author/commit dates | Git evidence | Repository chronology from August 11, 2026 onward |
| `Date: 2025` inside generated Markdown | Generated-document claim | Only that the text was present in the first commit; not when the described work occurred |
| Filesystem Created/Modified timestamps | Filesystem metadata | Local file-copy timing only; not used as contest chronology evidence |
| Fictional/test 2025 values | Synthetic data | LAST LIGHT story and test behavior, not project age |

## Scope and limits

This document records repository evidence. It does not backdate work, erase Git history, or substitute for the entrant's required personal eligibility and ownership confirmations under the Official Rules.
