# Submit Research to Open Math Progress

Open Math Progress supports public research submissions without
requiring contributors to write code, use Git, or open a Pull Request.

There are two distinct submission channels:

- **GitHub Issues:** Register mathematical problems and submit research
  contributions for automated indexing.
- **GitHub Discussions:** Publish research notices, attribution
  concerns, corrections, and open discussions.

OMP does not independently verify mathematical correctness,
originality, or scientific priority.

## 1. Register a New Mathematical Problem

If your mathematical problem is not listed:

1. Open [New Issue](https://github.com/tnflas/open-math-progress/issues/new/choose).
2. Choose **Register a New Mathematical Problem**.
3. Enter its title, mathematical statement, original reference,
   and field.
4. Submit the form.
5. Allow GitHub Actions to process the submission.
6. Find the resulting record in
   [Community Problems](COMMUNITY_PROBLEMS.md).

The assigned identifier has the form `OMP-U-N`, where N is
the GitHub Issue number.

Registration does not certify that the problem is new or open.

## 2. Submit Research to an Existing Problem

First locate the problem in:

- [Community Problems](COMMUNITY_PROBLEMS.md)
- [Research Index](INDEX.md)

Copy its exact OMP Problem ID.

Then:

1. Open [New Issue](https://github.com/tnflas/open-math-progress/issues/new/choose).
2. Choose **Submit Research Contribution**.
3. Paste the Problem ID.
4. Enter the contribution title.
5. List all authors, one per line.
6. Enter an abstract.
7. Select the reported research status.
8. Disclose the reported AI involvement.
9. Provide a public manuscript or attachment URL.
10. Submit the form.

GitHub Actions attempts to create a contribution record
and link it to the selected problem.

**If the problem is absent, register it first.**

A contribution can have multiple authors. Multiple contributions
may be submitted to the same mathematical problem.

## 3. How to Provide a Manuscript

The preferred method is to provide a public document link:

- Zenodo DOI or record URL
- arXiv URL
- GitHub document URL
- Another publicly accessible manuscript URL

Where GitHub permits, files may also be attached through its
Issue editor. Follow GitHub's current file type and size rules.

OMP stores manuscript links and submission metadata. It does
not automatically copy submitted PDFs or LaTeX files into Git history.

Only share materials you have permission to distribute.

## 4. Public Research Notices

Use [GitHub Discussions](https://github.com/tnflas/open-math-progress/discussions) for:

- Prior published research
- Independent or parallel work
- Academic attribution concerns
- Responses to earlier statements

Choose the **Research Notices** category.

These notices are public and unreviewed.

They do not establish ownership, authorship, misconduct, or
scientific priority.

Do not disclose confidential research or private correspondence.

## 5. Corrections and Responses

Use the **Corrections & Responses** Discussion category for
public research-related statements and responses.

For incorrect metadata, broken links, or software problems,
open a GitHub Issue or propose a Pull Request.

The repository does not adjudicate mathematical disputes.

## 6. Automation and Limitations

Automated indexing depends on GitHub Actions and supported
submission formats.

A submitted Issue does not guarantee successful indexing.
Check the generated community index and workflow status.

OMP does not independently assess mathematical proofs or determine
which researchers deserve priority.

**We record claims, not grant rights.
We preserve evidence, not judge priority.**
