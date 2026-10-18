# Hammer World development plan

Status: local fictional demo implementation and acceptance complete, including the PostgreSQL vertical slice, connected systems, four maps, private browser workflows, recovery and 10,000 persisted turns. See `docs/checkpoint.md` for observed results. PostgreSQL primary, Google Drive archives. Controlled JSON import works; authenticated MCP remains later work. External hosting and authenticated live Drive verification require later configuration. The real campaign remains pre-game unknown.

## Goal

Build a persistent browser-based Warhammer 40,000 grand-strategy command interface. ChatGPT acts as GM; the Linux backend calculates and commits approved numerical rules; the dashboard visualizes recorded state. The actual campaign starts pre-game with unknown statistics. A clearly labelled fictional demo is isolated from campaign data.

Current user-approved visual direction (18 October 2026): minimalist aerospace instrumentation, with off-white surfaces, graphite monospaced type, fine rules, alignment-led information groups and restrained selected controls. This supersedes the earlier Windows 95/98 visual direction. Retain the permanent map, compact command access, one management workspace and contextual inspector. The local demo supports Galactic, Sector, System and Planetary maps and management reports; unsupported real campaign fields remain unknown. See docs/reviews/instrument-design.md.

## 1. Housekeeping and agent hierarchy

- GPT-6 Luna (`gpt-6-luna`) is the main builder for bounded tasks with acceptance checks.
- Escalate localized implementation problems after one bounded failed attempt to GPT-6.1 Sol (`gpt-6.1-sol`) on medium.
- All major architectural decisions and important issues go to GPT-6.1 Sol on high: authority, schemas, security, simulation rules, integration, determinism and recovery.
- The coordinator assigns work and records decisions. Use compact briefs and targeted file context. Keep one builder active; add a specialist only when needed. Review major decisions once and reopen only with new evidence.
- Keep code lean. Prefer direct code, small modules and existing dependencies. Avoid speculative abstraction, microservices and generic simulation frameworks.
- Keep a short decision log, setup/recovery README, versioned schemas/rules/generators and reproducible fixtures. Keep secrets, databases, backups and runtime artifacts out of Git.
- Preserve applied migrations and committed history. Finish and verify a milestone before expansion. Report actual verification and blockers accurately.

## 2. Database and deterministic simulation core

Use a Linux modular monolith: Python/FastAPI, PostgreSQL (psycopg, direct SQL) and a thin frontend with pixel cartography. One backend owns campaign writes. The database is authoritative; Google Drive contains synchronized player-visible archives, ledger summaries and compact memory documents. Drive outages cannot invalidate a database commit.

Import existing records with provenance and validation. Explicitly record the authority migration before modifying existing campaign documentation; preserve old rules in the audit history. Later Drive edits never silently overwrite the database. The current Drive files are pre-game templates, not an approved numerical baseline.

Start with campaigns, provinces, resource accounts, facilities, orders, events, immutable snapshots and archive jobs. Records carry persistent IDs, turn, units, confidence, visibility, source events and rules version. Implement only structures required by the first slice.

Backend pure functions use integer/fixed-point arithmetic and versioned approved rules. Enforce resource conservation, production/consumption, labor allocation, industrial capacity, construction costs and time. Later modules enforce research prerequisites, recruitment, equipment, military losses, maintenance, transport capacity, travel delays and political modifiers.

ChatGPT provides strategic interpretation, diplomacy, event proposals and narrative. Narrative has no implicit mechanical effect. Mechanically consequential proposals must become validated commands; proposed balances or combat outcomes cannot bypass backend calculations. Fixture rules and values are explicitly fictional and do not establish real campaign canon.

## 3. Exact ChatGPT handoff

1. Export a versioned decision packet containing campaign ID, current revision, checksum, permitted context and available commands.
2. The player provides the packet to ChatGPT.
3. ChatGPT returns a JSON proposal containing commands, event proposals and separate narrative.
4. An authenticated GM/operator imports it through the controlled administration interface or authorized Linux CLI.
5. The backend validates the proposal and calculates a preview.
6. The operator commits the validated preview.

Each proposal references the source revision and an idempotency key. Reject stale packets. Duplicate imports cannot resolve twice. Ordinary ChatGPT messages have no server access. Later MCP tools (`get_decision_packet`, `submit_proposal`, `get_preview`, `commit_turn`) use the same pipeline and must be authenticated and verified before automatic integration is claimed.

## 4. One generated planet and command interface

Build one planet with persistent provinces, terrain, settlements, facilities and resource accounts. Support selection, tooltips, zoom/pan and relevant overlays. Show fictional demo statistics separately from the unknown pre-game campaign.

Generation follows Universe -> Galactic region -> Sector -> System -> Planet -> Geography. Derive versioned sub-seeds using stable parent IDs and domain labels, independently of traversal order. Persist IDs, configuration, generator version and initial geography. Never regenerate established data during loading. Construction, warfare, exploration and other changes create recorded revisions. Keep campaign seeds and undiscovered output server-side.

## 5. Atomic saves, recovery and safe archives

One database transaction checks the base revision, validates/calculates the turn, stores inputs/outcomes/events and an immutable full snapshot, advances current state and enqueues a Drive archive job. Commit all or none.

A retryable outbox uses stable identifiers and checksums. Distinguish database committed, archive pending and archive verified. Drive is not part of the database transaction. Use full snapshots initially; add checkpoint/delta machinery only when measurements justify it.

Historical inspection is read-only. Restore creates a new branch and preserves the original timeline. Corrections create audited revisions. Include backup/restore commands and test actual database recovery.

GM data stays behind separate authorization and explicit player response schemas. No hidden seeds, movements, confidential source references or future outcomes in player APIs, frontend files, browser storage or player-visible archives. Filter before serialization, including histories, search, exports, errors and counts. Genuine secrecy from the Linux operator requires an independently operated GM vault.

## 6. Vertical-slice acceptance gate

Demonstrate one generated planet -> functioning economy -> ChatGPT JSON proposal -> one backend-calculated turn -> validated save -> historical restoration.

Test determinism; stale/invalid/duplicate proposal rejection; balances and capacity; no partial interrupted commit; recoverable Drive failures; exact snapshot restore; hidden-marker exclusion; campaign/demo isolation; and actual backup recovery.

Run at least 10,000 synthetic fixture turns, measuring conservation, historical correctness, storage growth and queries. Do not modify the live campaign. Expand only after the gate passes; identify any unverified integration explicitly.

## 7. Incremental expansion

Add System, Sector and Galactic maps using the same hierarchy and visibility model, then construction, research, logistics, military, politics, diplomacy and remaining management views. Use chunking and zoom-dependent detail when data warrants it. Add approved rules, historical records and meaningful tests per module. Extend stress tests to interconnected shortages, transport delays, workforce competition, recruitment and maintenance.

## 8. Private deployment and operations

Local completion does not require a hosting provider, domain or live Drive connection. Keep those settings and database credentials configurable. Proposed real Drive archive folder: **Wold — Campaign Archives**; demo archives require a separate destination.

Deploy with authenticated player/operator access, TLS, automated backups, tested recovery and visible synchronization status. The first slice runs locally on Linux; public/private remote hosting must enforce the intended audience. Never claim an unconfigured Drive connection or unpublished deployment is live.

Backend owns calculations and commits. ChatGPT owns GM proposals and interpretation. Drive archives results. Optimize observed bottlenecks; introduce additional infrastructure only when measured requirements justify it.

## Existing campaign sources

- Memory: https://docs.google.com/document/d/1dDT1U8J5hdOUMMM-ypxLl5G8cjv5bePRm9FbUE-6QTE/edit
- Ledger: https://docs.google.com/spreadsheets/d/1xX8qBX_XVj-G0_Q8Pb9yyhQRokGFl28GePFVmDTyDG8/edit
- Chronicle: https://docs.google.com/document/d/1Cr2SgGyOmF9mtbnSy8W5SNBQ-6AXOfeFmjZF2vT2edY/edit

These are reference/pre-game sources until explicitly migrated. No approved planet, statistics or saved turns currently exist in them.
