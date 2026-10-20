# Problem-Centered Contribution Structure

Open Math Progress organizes research around mathematical problems.

## Problem Records

A problem has a stable identifier and may contain contributions from
multiple independent researchers.

## Contributions

Each contribution has its own identifier, author list, reported status,
original submission link, and manuscript links.

Example:

```text
problems/
  community/
    omp-u-1/
      metadata.json
      README.md
      contributions/
        omp-c-i-2/
          metadata.json
          README.md
```

This illustrates the current storage layout; `community/` is an
implementation detail, not a separate type of mathematical contribution.

## How to Submit

**Contributors do not need to write code.**

Use the [Submission Guide](SUBMISSION_GUIDE.md) to register a mathematical
problem or submit a research contribution through GitHub Issue Forms.

## External Research

Research imported from external sources may be represented by metadata
and original-source links rather than copied PDF files.

## Versioning and Verification

Contributions may have revised manuscripts. Preserve original source
links and distinguish reported claims from independently checked results.

OMP does not determine mathematical correctness, novelty, or priority.
