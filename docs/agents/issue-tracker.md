# Issue tracker: GitHub

Issues and specifications for this project live in GitHub Issues in
`pavelkrotkov/film-iq`. Use the `gh` CLI from this repository or its worktrees.

- Read a ticket and its discussion: `gh issue view <number> --repo pavelkrotkov/film-iq --comments`.
- List open tickets: `gh issue list --repo pavelkrotkov/film-iq --state open`.
- When a skill says to publish to the issue tracker, create a GitHub issue in
  `pavelkrotkov/film-iq`; use a body file for multiline text.
- Preserve the existing epic links, acceptance criteria, and label vocabulary.

`plan.md` is the authoritative product and phased engineering reference.
Read the originating issue and relevant decisions in `docs/adr/` when reviewing
a change. A missing or inaccessible issue is unknown; do not invent its requirements.
