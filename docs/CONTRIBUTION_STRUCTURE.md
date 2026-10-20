# Problem-Centered Contribution Structure

OMP supports multiple independent contributions to the same problem.

## Directory Layout

```text
problems/
  problem-slug-id/
    README.md
    metadata.json
    contributions/
      OMP-C-xxxxxxxxxxxx/
        README.md
        metadata.json
        versions/
          v1/
            paper.pdf
            paper.tex
```

Each contribution has a stable contribution ID.

One contribution may have multiple authors and versions.

Research notices remain public GitHub Discussions. They are not
automatically treated as verified priority claims.

## Existing Problems

Use an existing ID from `data/problems.json` when adding contributions.

The current external index may contain several problem candidates
for the same mathematical question. Similar titles do not justify
automatic merging.

## Add a Contribution

Example:

```bash
python3 scripts/add_contribution.py \
  --problem-id "OMP-EXISTING-ID" \
  --title "Research Progress" \
  --author "Author Name" \
  --paper "/path/to/paper.pdf"
```

The ID in this example must be replaced by an actual ID.

You may provide `--author` more than once for joint work.

## Versioning

The initial submission creates `versions/v1/`.

Later versions must preserve earlier files where legally and
technically appropriate. Do not overwrite a published version
without updating its metadata.

## Licensing

Only upload papers and attachments you have permission to publish.

For external research, prefer links rather than copying third-party PDFs.

## Verification

The contributor reports the research outcome.

OMP does not independently verify mathematical correctness,
originality, or scientific priority.
