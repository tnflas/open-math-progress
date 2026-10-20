# Methodology

## 1. Purpose and Scope

Open Math Progress (OMP) is an independent, automated index of publicly reported mathematical research progress, including AI-assisted discoveries.

OMP records source-reported mathematical claims and links to their origins.

**OMP does not independently verify mathematical correctness, novelty, completeness, or scientific priority.**

The index is not an authoritative list of solved mathematical problems.

## 2. What We Collect

Depending on the available source format, OMP may collect:

- Reports claiming complete solutions or counterexamples.
- Partial mathematical results.
- Source-reported research updates.
- Disputed or retracted claims.
- Public Research Notices submitted through GitHub Discussions.

Inclusion depends on source availability, adapter support, and automated filtering rules. It is not comprehensive.

## 3. Data Sources

Sources are registered in `data/sources.json`.

Each source may require a separate adapter. Supported formats may include:

- Explicitly labeled GitHub Issues.
- Structured Markdown research indexes.
- Selected problem-status catalogues.
- Structured JSON feeds.

A source being listed does not guarantee that all its contents are indexed.

The actual enabled sources and their configured modes are documented in [Source Coverage](docs/SOURCE_COVERAGE.md).

## 4. Collection Pipeline

The general process is:

1. Read the source registry.
2. Fetch supported public source data.
3. Extract records matching the adapter's rules.
4. Normalize source metadata.
5. Match source records using stable identifiers.
6. Update stored claims and their observed status changes.
7. Validate data structure and references.
8. Generate public Markdown indexes.

The precise behavior depends on the implementation in `scripts/`.

The process does not assess mathematical proofs.

## 5. Data Model

OMP distinguishes four conceptual objects.

### Mathematical Problem

A research question or problem candidate.

An OMP problem record does not necessarily correspond to a globally unique mathematical problem.

Different source records may refer to the same problem.

### Research Claim

A source-reported mathematical result, such as a claimed proof, counterexample, or partial theorem.

One mathematical problem may have several distinct research claims.

### Research Event

A source-reported development relating to a problem.

For example, an event may report that a partial theorem was proved even when the original problem remains open.

An event type is not equivalent to the status of the entire mathematical problem.

### Public Research Notice

A contributor-submitted statement concerning prior work, parallel research, attribution, or corrections.

Such notices are unreviewed and do not establish academic priority or ownership.

The current implementation may represent some of these conceptual objects within a single stored claim rather than as separate database tables.

## 6. Research Status

Status labels report statements from the original source.

They are not OMP certifications.

| Stored label | Meaning |
|---|---|
| `claimed_solved` | A source reports a resolution or a result classified by its adapter as resolving the stated target. |
| `partial_progress` | A source reports partial progress. |
| `disputed` | A source reports a contested result. |
| `retracted` | A source reports withdrawal or retraction. |
| `not_assessed` | OMP has not evaluated the mathematical result. |

Adapters may preserve more specific reported outcomes such as `proved`, `refuted`, `counterexample`, or `nonexistence`.

A counterexample refutes a statement; it does not prove that original statement.

A proof of a restricted case does not automatically resolve the unrestricted problem.

A source-reported resolution does not imply acceptance by the mathematical community.

## 7. Verification Evidence

OMP distinguishes:

1. Evidence reported by the original source.
2. Independent mathematical verification, which OMP does not perform.

Original sources may report:

- Author checks.
- AI-based review.
- Human expert review.
- Peer review.
- Formal proof files or kernel checking.

OMP does not automatically authenticate such reports.

Even formal verification claims require attention to whether the checked statement matches the intended mathematical problem.

The `not_assessed` label describes OMP's own verification status, not necessarily the source's evidence.

## 8. AI Involvement

AI participation is recorded only to the extent supported by the source metadata.

Possible distinctions include:

- AI involvement explicitly reported for an individual result.
- Inclusion in a collection focused on AI research.
- Unknown or undisclosed AI involvement.

These are not equivalent.

OMP does not infer AI authorship from writing style.

AI involvement alone does not establish or invalidate the novelty of a mathematical contribution.

## 9. Identity and Deduplication

OMP aims to prevent repeated imports of the same source record.

Source URLs and stable upstream identifiers are important matching keys.

Important limitations:

- Identical research titles do not establish identical mathematical statements.
- Identical DOIs may identify the same paper without identifying the same mathematical problem.
- Different URL fragments may identify distinct entries in one Markdown document.
- Distinct sources may discuss the same mathematical problem.

Automatically matched records must not be treated as decisions about scientific priority.

The current implementation may create separate problem candidates for separate sources.

Potential duplicate flags do not establish mathematical equivalence.

## 10. Updates and Retractions

OMP attempts to preserve observed changes in source-reported status.

A status history is a record of what OMP observed and when, not necessarily the first publication date or discovery date.

If an upstream claim is retracted, the index should preserve the reported retraction rather than continuing to present the claim as uncontested.

Temporary request failures must not be interpreted as retractions.

Historical records created by earlier adapter versions may contain limitations inherited from those versions.

## 11. Public Research Notices

Research Notices are independently submitted statements.

The repository does not authenticate a submitter's scholarly identity, adjudicate conflicting statements, or certify priority.

Notices can link to research problems, but such links are organizational references only.

Researchers should not disclose unpublished or confidential materials unless they are willing and authorized to make them public.

See [Research Ethics](RESEARCH_ETHICS.md) and [Submission Guide](docs/SUBMISSION_GUIDE.md).

## 12. Coverage and Failure Modes

The index is incomplete by design.

Possible causes of missing or inaccurate entries include:

- Unsupported source formats.
- Changed upstream data structures.
- API errors or rate limits.
- Incomplete metadata.
- Ambiguous problem identity.
- Adapter parsing mistakes.
- Delayed upstream corrections.
- Source documents that do not explicitly distinguish full and partial progress.

A successful GitHub Actions run only confirms completion of the configured software workflow.

It does not establish complete source coverage or mathematical correctness.

## 13. Reproducibility

The index is maintained using repository scripts.

Typical local commands:

```bash
python3 scripts/core.py validate
python3 scripts/core.py generate
python3 scripts/core.py all
```

The last command may access public network resources and update generated data files.

Before running a synchronization, inspect the enabled sources in `data/sources.json`.

Exact outputs may change as upstream repositories are updated.

## 14. Limitations and Non-Goals

OMP does not:

- Certify mathematical theorems.
- Decide whether a famous conjecture has been resolved.
- Determine originality or research priority.
- Award authorship or research ownership.
- Rank researchers or AI systems.
- Guarantee comprehensive coverage.
- Replace original publications, archives, or scholarly review.

**We record claims, not grant rights. We preserve evidence, not judge priority.**
