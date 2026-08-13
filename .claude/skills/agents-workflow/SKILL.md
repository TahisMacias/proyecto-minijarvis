---
name: agents-workflow
description: Low-token .agents/ project workflow with executor/auditor separation and risk-scaled assurance. Eight jobs - INIT, MAINTAIN, AUDIT, RUN THE LOOP, CLOSE, COMPACT, REINDEX, and EXPORT DOCUMENTATION. Use for setup, repair, delivery review, bounded execution, closure, context reduction, index repair, or a dated human-readable snapshot.
---

# agents-workflow

Manage a software project through a small, versioned `.agents/` control plane.
The workflow targets beginners, small or medium applications, and basic AI
subscriptions. It values recoverability, explicit state, and evidence without
requiring a large agent platform, vector database, or permanent audit conversation.

## Dispatch first

Choose exactly one job from the user's request and current repository state:

| Job | Use when | Result |
|---|---|---|
| **INIT** | A project has no usable `.agents/` | Create the control plane without overwriting product work |
| **MAINTAIN** | Existing planning or documentation is stale, broken, or inconsistent | Repair control state without pretending to initialize or close work |
| **AUDIT** | An executor reports STOP/DONE or a review is requested | Verify scope, evidence, risks, and state; return APTO or NO APTO |
| **RUN THE LOOP** | The user wants continuous execution and review | Alternate bounded execution and audit until a terminal condition |
| **CLOSE** | A milestone is verified and ready to archive | Reconcile state, archive the plan, and record closure |
| **COMPACT** | `.agents/` has become expensive to load | Summarize old detail while retaining decisions and traceability |
| **REINDEX** | Files, plans, or repository layout changed materially | Rebuild indexes and cross-references from repository facts |
| **EXPORT DOCUMENTATION** | A human needs a readable project snapshot | Generate root `DOCUMENTATION.md` from current verified knowledge |

Do not run INIT merely because `.agents/` is imperfect. Use MAINTAIN.
Do not run CLOSE merely because code was committed. Audit first.

## Assurance profile

Select the cheapest profile compatible with actual risk. Record the selection in
`.agents/AGENTS.md` or `.agents/CURRENT.md`.

- **Lean is the default and recommended profile.** Run deterministic gates for each
  product commit. Use a model audit only for risky tasks, phase boundaries, failed
  gates, or release. Batch adjacent low-risk tasks when their scopes do not overlap.
- **Standard** adds an independent model audit at each milestone and selected tasks.
- **Strict** audits every task independently and adds domain-specific gates. Use only
  for high-impact, regulated, security-sensitive, financial, medical, destructive,
  or explicitly requested work.

An audit must consume an **audit capsule**, not the whole project by habit. The capsule
contains: task ID and acceptance criteria, base/head commits, changed-file list, compact
diff or exact diff command, gate results, relevant risks, and unresolved questions.
Expand context only when evidence is missing or a risk crosses the capsule boundary.

## Two planes, two commit classes

- The **product plane** is owned by the executor: application code, tests, assets, and
  task-specific product documentation.
- The **control plane** is owned by the planner/auditor: `.agents/`, indexes, audit
  records, exported snapshots, and workflow repairs.

Product work uses one focused commit per task with `[T-NN]` in the subject.
Control-only work uses `[STATE]`. A closure, compaction, reindex, repair, or documentation
export may therefore be a separate `[STATE]` commit without violating one-task-one-commit.
Never hide product changes inside `[STATE]`.

The auditor may directly edit only the control plane. Product-plane corrections require
a new or reopened task brief for the executor. If a requested fix changes product scope,
acceptance criteria, architecture, security behavior, or external interfaces, STOP and
create/revise the task before implementation.

## Minimal control plane

Keep these files under `.agents/`:

```text
.agents/
  AGENTS.md
  APPCORE.md
  CURRENT.md
  CONTEXT.md
  INDEX.md
  TESTING.md
  PLAN_vX.Y-name.md
  archive/
```

- `AGENTS.md`: repository rules, assurance profile, roles, commands, boundaries.
- `APPCORE.md`: stable purpose, users, constraints, architecture, and invariants.
- `CURRENT.md`: concise present state, active plan/task, blockers, next action.
- `CONTEXT.md`: chronological decision and handoff log.
- `INDEX.md`: map of active files, plans, important code, and archives.
- `TESTING.md`: deterministic checks plus human validation matrix.
- `PLAN_vX.Y-name.md`: milestone tasks, dependencies, acceptance, status.
- `archive/`: closed plans and displaced detail that must remain traceable.

Create only additional files that reduce repeated context. Avoid copying the same facts
into several files. Stable truth belongs in APPCORE; changing truth belongs in CURRENT;
history belongs in CONTEXT; executable scope belongs in the active plan.

`CONTEXT.md` is append-only during normal INIT, AUDIT, RUN THE LOOP, and CLOSE work.
Only COMPACT or an explicitly scoped MAINTAIN may rewrite, compress, or summarize old
entries. Preserve dates, decisions, task/commit references, unresolved risks, and a
pointer to any archived source. Never silently revise historical meaning.

## Portability and boundaries

- Persist **repository-relative** paths. Resolve the repository root at dispatch time.
  Absolute paths may appear in transient commands, never in durable briefs or recipes.
- Discover and record **sibling** systems and ownership boundaries during INIT. Do not
  read, edit, or audit a sibling repository unless the current integration requires it
  and the user has placed it in scope.
- Require **local Git** for durable checkpoints. A **remote is optional**; ask whether the
  owner wants local-only Git, a remote, or another external backup, then record the answer.
- Treat the repository as factual authority. `.agents/` is the planning authority only
  after conflicting claims have been checked against code, configuration, tests, and Git.
- Never store credentials, tokens, private keys, personal data, or environment secrets in
  `.agents/`, exported documentation, commits, or audit capsules.

## Read budget

Start with the smallest useful set:

1. Repository instructions and status/diff.
2. `.agents/CURRENT.md` and the active plan.
3. Relevant parts of `AGENTS.md`, `APPCORE.md`, `TESTING.md`, and `INDEX.md`.
4. Product files named by the task or changed by the commit.
5. `CONTEXT.md` and archive only when history is material.

Search before reading large files. Read complete files only when their whole contract is
needed. Reuse deterministic commands and compact outputs. Do not repeatedly ingest the
entire repository to gain confidence.

## INIT

1. Confirm the repository root and inspect existing instructions, code, Git state, and
   any partial `.agents/` before writing.
2. Ask only unresolved decisions that materially change the workflow: product goal,
   immediate milestone, assurance profile, sibling-system access, Git/backup choice,
   irreversible constraints, and human validation needs.
3. Create the minimal control plane from verified repository facts. Preserve existing
   content; merge or use MAINTAIN when a control plane already exists.
4. Build an active milestone plan with small tasks, dependencies, acceptance criteria,
   likely files, tests, risk triggers, and STOP conditions.
5. Set CURRENT to one next action. Validate links and referenced files.
6. Commit control state as `[STATE] init agents workflow` when authorized.

## MAINTAIN

1. Inventory `.agents/`, its references, current Git facts, and affected product files.
2. Classify each defect: missing, stale, contradictory, duplicate, broken reference,
   absolute path, unsafe content, or misplaced history.
3. Apply precedence: repository facts; CURRENT; APPCORE; AGENTS; active plan; TESTING;
   CONTEXT; archive. Newer text does not override verified reality automatically.
4. Repair only the control plane. Preserve product code and unrelated user changes.
5. If history needs rewriting, declare MAINTAIN as compaction-capable, preserve an archive
   or traceable summary, and state what was replaced.
6. Run coherence and link checks. Record repairs in CONTEXT and commit `[STATE] maintain ...`.

## AUDIT

1. Establish task, acceptance criteria, base/head commits, selected assurance profile,
   and whether the working tree contains unrelated changes.
2. Read the audit capsule. Inspect the exact diff and expand only for unresolved evidence.
3. Check scope, behavior, tests, security triggers, documentation impact, and repository
   state. Do not accept summaries as proof.
4. Run or inspect deterministic gates appropriate to the project. Record command, result,
   and relevant output. Mark unavailable gates honestly.
5. Return one verdict:
   - `APTO`: criteria met, evidence sufficient, no unresolved blocking risk.
   - `NO APTO`: list concrete defects with file/location, impact, and required correction.
   - `BLOCKED`: required evidence or authority is unavailable.
6. Update control state only. Product fixes become a new/reopened executor brief.

## RUN THE LOOP

Repeat this bounded state machine:

```text
select ready task -> dispatch brief -> executor commit/STOP -> deterministic gates
-> risk-scaled audit -> APTO advances | NO APTO reopens | BLOCKED asks owner
```

Before dispatch, require: task ID, objective, allowed scope, acceptance criteria, checks,
dependencies, risks, and STOP conditions. A brief must be self-contained but compact and
must use repository-relative paths.

Stop when the milestone is complete, the owner asks, no task is ready, three correction
cycles fail for the same cause, scope/authority is missing, or a safety boundary is hit.
Do not simulate independence by accepting the executor's own claim without evidence.

## CLOSE

1. Require APTO for all milestone tasks and completion of required human checks.
2. Compare plan, CURRENT, TESTING, code, and Git. Remove contradictory stale status such
   as the same dependency being both installed and missing.
3. Run a stale-state sweep: task statuses, active plan link, versions, dependencies,
   commands, known issues, and indexes.
4. Record outcome, remaining risks, deferred work, and release/backup state.
5. Move the closed plan to `.agents/archive/`, rebuild INDEX, set CURRENT to the next real
   action, append CONTEXT, and commit `[STATE] close ...`.

## COMPACT

1. Measure which files create repeated token cost. Do not compact merely for aesthetics.
2. Preserve active requirements, current facts, decisions with rationale, unresolved
   risks, task/commit IDs, and recovery pointers.
3. Move obsolete detail to a dated archive or replace it with a traceable summary.
4. Rewrite CONTEXT only under the exception defined above. Mark the compaction boundary
   and archive location.
5. Rebuild INDEX, verify references, and commit `[STATE] compact ...`.

## REINDEX

Re-scan the repository and `.agents/`; then rebuild INDEX links, active-plan references,
important-code pointers, archive entries, and relevant commands. Detect missing targets,
duplicate phase responsibilities, and stale names. REINDEX changes navigation, not product
scope. Commit `[STATE] reindex ...`.

## EXPORT DOCUMENTATION

Generate root `DOCUMENTATION.md` as a **point-in-time snapshot**, not living documentation.
Read all of `.agents/`, including CONTEXT and archive; use this precedence for conflicts:
repository facts, CURRENT, APPCORE, AGENTS, active plan, TESTING, CONTEXT, archive.

Verify claims likely to drift: current behavior, commands, dependencies, versions, active
limitations, and important paths. Then **sanitize** secrets, personal data, internal-only
details, unsafe commands, and stale absolute paths.

The exported document must be understandable without `.agents/` and include:

```yaml
generated_at: ISO-8601 timestamp with timezone
source_commit: Git commit hash, plus dirty state when applicable
workflow_version: installed agents-workflow version if known
audience: technical-collaborator
```

Include purpose, current capabilities, architecture at a useful level, important code,
setup/build/run/test instructions, operational workflows, limitations, known risks, and
the snapshot warning. Default `audience` is `technical-collaborator`; adapt it if the user
names another audience. Do not expose private audit chatter unless it aids the audience.
If committed, use `[STATE] export documentation`.

Remind the owner that EXPORT DOCUMENTATION is available when the project grows, before a
handoff, or when a human collaborator needs context. Do not keep `DOCUMENTATION.md`
continuously synchronized unless the owner explicitly requests a new export.

## Conditional quality checks

Apply checks only when the feature creates the risk:

- **Trust boundary:** for licensing, authentication, cryptography, distributed clients,
  signatures, secrets, or privileged services, identify who holds authority and secrets.
  Never place a verification secret in an untrusted client. Prefer public-key verification
  when offline verification must not grant signing power.
- **Protocol round trip:** for request/response, pairing, WebRTC, QR exchange, callbacks,
  queues, or handshakes, trace both directions, timeouts, retries, cancellation, and errors.
- **Phase coherence:** compare tasks and modules across phases for duplicated ownership,
  conflicting types, incompatible schemas, or a dependency scheduled after its consumer.
- **State coherence:** at audits and closure, search for mutually incompatible current
  claims and verify them against the repository.

These are prompts for reasoning, not mandatory technologies or algorithms.

## Tool recipes

Do not encode volatile CLI flags as universal workflow law. Keep tool commands in a dated,
project-local recipe with tool/version, operating system, working directory, permission
model, tested command, expected output, and last verification date. Re-verify a recipe after
tool upgrades. Prefer least privilege; scope filesystem access to the repository.

## Non-negotiable behavior

- Preserve unrelated user changes and inspect before overwriting.
- Never claim a test, audit, or command ran unless evidence exists.
- Never weaken acceptance criteria silently to obtain APTO.
- Never let planning files overrule verified product reality.
- Keep active state concise; keep history recoverable.
- Escalate product, security, scope, ownership, or destructive decisions to the owner.
