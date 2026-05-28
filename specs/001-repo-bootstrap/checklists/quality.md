# Quality Audit Checklist

Source: review.md (3486bf2)

- [ ] R1 — tasks.md missing: branch is mid-workflow — run /speckit-tasks then /speckit-analyze before /speckit-implement (`specs/001-repo-bootstrap/`)
- [ ] R2 — Coverage gate downgraded without constitutional amendment — add `--cov-fail-under=80` to pytest config or open a PATCH amendment to constitution.md (`specs/001-repo-bootstrap/plan.md:108-112`)
