# Zero-debt doctrine — bookwright-quality workflow

Single source of truth for the anti-debt rules every `type: prompt` step in
`workflow.yml` applies. Each such step begins by reading THIS file and then
acts on it, so the doctrine lives in one place (Principle I, plain text) and
cannot drift across the steps that share it. The repository references that
specs and prompts cite — `.specify/memory/constitution.md`, `CLAUDE.md`,
`bookwright-design.md`, `DEBT.md` — are the binding context; this file only
distills the decision rules the autonomous run must apply without asking.

## 1. Decide by the Constitution Check gate, never by asking

Every judgement call (clarification answers, finding resolutions, what to fix,
what to defer) is resolved against `.specify/memory/constitution.md` and
`CLAUDE.md` — not by asking the user and not by taking a shortcut. The three
NON-NEGOTIABLE principles are the deciding criteria:

- **I — plain-text source of truth.** The graph is ALWAYS a derived cache,
  reconstructible from `bible/*.md` etc., never the source.
- **VI — Agent Skills only.** Emit one `SKILL.md` per command; never write to
  `.claude/commands/` or any analogue.
- **VIII — test discipline.** ≥80% coverage, single-sourced in
  `[tool.coverage.report]` (`fail_under = 80`); never add `--cov-fail-under`.

Also binding: the **Scope & Release Discipline** rule and the four CI gates —
`uv run ruff check`, `uv run ruff format --check`, `uv run mypy --strict`,
`uv run pytest`.

## 2. Keep the iteration to one observable delta (scope discipline)

A spec/plan/diff that adds plumbing whose only justification is "future X" must
be rewritten to drop it. Do not implement, refactor, or specify ahead of the
plan.

## 3. Zero NEW debt — eliminate the cause, don't contain it

If the contract as drafted (or the code as written) would prescribe a smell —
an unused param, an internally-inconsistent assertion, a "small impurity", a
deferred "follow-up", a guard / allowlist entry / suppression / justification
comment / synthetic test that exists only to make a smell "safe" — first check
whether the **cause can simply be deleted** so no guard is needed at all. A
removed cause beats a justified guard. The autonomous cycle tends to "contain
the smell with a justified guard"; actively look for the deletable cause
instead, then remove it now rather than carry it.

## 4. Debt is a CLASS — sweep every instance, repo-wide

When you touch a known debt class, fix EVERY instance of that class across the
whole repository — even files outside this iteration's diff — not just the
single cited location. Precedent: iteration 027 unified ALL JSON envelopes, not
the one cited. Sweeping a class you are already touching is NOT widening scope;
it is the correct fix.

## 5. The only debt you may leave — and you must record it, never drop it

The ONLY debt left unfixed is debt of a DIFFERENT, unrelated class whose
cleanup would genuinely be its own iteration. Even then you MUST NOT silently
drop it: append an entry to the repo-root `DEBT.md` ledger AND report it loudly
in your output. The ledger entry carries: status, detected-in `spec-<NNN>`,
location, debt class, description, why-deferred, suggested resolution / target
version. Found debt is never left untracked.
