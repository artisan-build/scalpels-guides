# Improvement ledger

## Last run

- finished_at: never
- covered_until: 2026-10-15T00:00:00Z

## Apps

Each tool lives on its own Scalpels deployment, so each has its own `app_deployment`. The app
identifiers are exactly what each tool's list call returns: Hone's `list-apps-tool` display name,
including its `(production) [env-…]` part, and Wake's `list_apps` id rather than the name beside it.
Copy them; do not reconstruct them from something that looks right.

| Name | Repository | Scalpels team | Hone app_deployment | Hone app | Wake app_deployment | Wake app |
| --- | --- | --- | --- | --- | --- | --- |
| Storefront | acme/storefront | acme | … | … | pending | pending |

A cell marked `pending` means that tool is not installed or connected yet: skip that tool for that
app and say so in the summary. It is not a read failure and does not hold `covered_until` back.

## Open findings

| Fingerprint | Todo | Issue | First seen | Last seen | Hits |
| --- | --- | --- | --- | --- | --- |

## Runs

<!-- One line per run, newest last. -->
