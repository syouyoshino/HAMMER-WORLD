# Working rules

Read `plan.md` before changing behavior. PostgreSQL is primary; Drive archives. SQLite is only a legacy read-only migration input. Real campaign values remain unknown until approved. All seeded examples are demo fixtures.

## Agent hierarchy

- Main builder: `gpt-6-luna`.
- One unsuccessful bounded implementation attempt: escalate the localized issue to `gpt-6.1-sol`, medium.
- Major architecture decisions/issues: `gpt-6.1-sol`, high. This includes authority, schema, security boundaries, numeric rules, contracts, determinism and recovery.
- Use `fork_turns="none"` with a compact task brief when selecting models. Keep one builder active; add one specialist only as needed. Do not repeat broad reviews without new evidence.

## Housekeeping

- Keep modules small and direct. Avoid premature generalization and new dependencies when existing ones suffice.
- Bound scope to the first vertical slice until its acceptance checks pass.
- Never commit credentials, runtime databases, backups or generated artifacts.
- Never silently mutate history or treat unknown as zero.
- Do not expose hidden state or generation seeds in player-facing responses or client code.
- Keep simulation calculations on the backend, using versioned integer/fixed-point rules.
- Preserve schema migration history. Record significant decisions in `docs/decisions.md`.
- Run meaningful targeted tests; broaden when changes or failures justify it. Include the 10,000-turn fixture stress gate.
- Do not claim Drive sync, authentication, deployment or browser QA has passed without observing it.
