# REMEDIATION.md

Copy this to the root of each repository the loop works on, and change it to suit that project.
Investigators read it before they change anything.

Level: draft-pr

- Always start with a failing test that reproduces the problem.
- Run the project's full checks before opening a pull request. Do not open it if anything fails.
- Open pull requests as drafts, linked to the issue with "Fixes #N".
- Performance fixes that only add an eager load, an index or a cache may be marked ready and
  merged once CI is green.
- Never change files under app/Billing, database/migrations or config/, and never add or upgrade a
  dependency. Stop and comment on the issue instead.
