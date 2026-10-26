# Publication readiness and human inputs

This page separates preparatory artifacts from actual external publication.
The v0.8.1 software archive is published on Zenodo. No PyPI upload, journal
submission or acceptance is established.

Main is now the unreleased 0.8.2.dev0 usability patch. Its separate development
version does not rewrite the v0.8.1 archive. CITATION.cff deliberately cites the
released v0.8.1 record; no development-snapshot DOI is claimed.

## Published software pre-release

[v0.8.1](https://github.com/ysmhla/alga-twin/releases/tag/v0.8.1) is published on GitHub
as an ALPHA pre-release from f2db7f8ebd4c3d000e2441094f5f2934ec90dd2d. Four
assets are available: wheel, complete source archive, installed-wheel evidence
and SHA-256 manifest. GitHub-reported digests matched all four local uploads.
The same four checked files are now preserved in the Zenodo software archive
described below. No PyPI upload or journal acceptance is claimed.

[Exact release-source CI 40292325912](https://github.com/ysmhla/alga-twin/actions/runs/40292325912)
passed Python 3.12: 156 tests/Ruff and both tutorials; Python 3.11: 145 tests/one
optional skip/Ruff. Distribution CI 40292325963 and docs deployment 40292325816
passed. The release tag is preserved; this later publication record changes no
model code or release artifact. Human scholarly review remains pending.

## Published Zenodo software archive

[Record 23665342](https://zenodo.org/records/23665342) was published on 2026-10-26,
resource type Software, version 0.8.1, creator Ram Yash, MIT licence, alpha/WIP.

- Version DOI: [10.5281/zenodo.23665342](https://doi.org/10.5281/zenodo.23665342), for the exact archived release.
- Concept DOI: [10.5281/zenodo.23665341](https://doi.org/10.5281/zenodo.23665341), for all versions; it currently resolves to v0.8.1.

Both DOI links were followed separately and resolved to the published record.
Its actual JSON export reports `is_published: true`, `is_draft: false`,
`status: published`; all four file sizes and Zenodo MD5 checksums match the local
GitHub release assets. The evidence also records their local SHA-256 values.
[Publication evidence](smoke/v0_8_1/zenodo_evidence.json) and
[published-record screenshot](https://github.com/ysmhla/alga-twin/blob/main/assets/screenshots/zenodo-v081.jpg).

The manual deposit preserves the original release files. Their embedded
pre-deposit documentation has the earlier DOI-pending status; main-branch
CITATION.cff/docs record the later verified DOI. The published tag and files were
not rewritten or rebuilt. No biological validation or human-study claim follows
from archival publication.

## Verified preparation

Earlier packaging-tested source: 2b303b502f9c7236c7cdfa6961d83ee6279c4979.
Distribution checks on Python 3.11 and 3.12 passed in
[CI 40290016328](https://github.com/ysmhla/alga-twin/actions/runs/40290016328),
including actual installed-wheel API/CLI/refusal/N-ledger checks. Strict docs
build passed in [CI 40290016434](https://github.com/ysmhla/alga-twin/actions/runs/40290016434).
Scientific checks and exact counts are in VERIFICATION.md. GitHub Pages is
configured to use Actions; public docs deployment passed in [run 40291099481](https://github.com/ysmhla/alga-twin/actions/runs/40291099481).
The site was opened and its home/navigation verified at https://ysmhla.github.io/alga-twin/ .
Zenodo authentication and manual archival publication were subsequently completed;
see the published-record evidence above.

## Available artifacts

- Semantic project version and CHANGELOG; source/wheel build configuration.
- Separate PyPI README with absolute links and explicit scientific limitations.
- MIT licence and schema-valid CITATION.cff; no invented DOI/ORCID/affiliation.
- Documentation site source and strict link/build verification.
- `paper.md` / `paper.bib` JOSS-style draft, including limitations and AI disclosure.
- [Related-work table](RELATED_WORK.md), explicitly HUMAN REVIEW PENDING.

The wheel provides the core Python API/CLI. Dashboard, benchmark files, notebooks
and documents are included in the source archive. Optional benchmark dependencies
require Python 3.12; core remains Python 3.11+. Package checks cannot validate
biological predictions. Use VERIFICATION.md for the actual observed check scope.

## Build and inspect

```bash
python -m pip install 'build>=1.2,<2' 'twine>=6,<7'
python -m build
python -m twine check --strict dist/*
python -m pip install 'cffconvert>=2,<3'
cffconvert --validate
python -m pip install 'mkdocs>=1.6,<2'
mkdocs build --strict
```

Run publication tooling separately from benchmark/scientific dependencies:
`cffconvert` currently constrains an older jsonschema series. A clean wheel
installation outside the source checkout must import the installed package,
execute the CLI and preserve the synthetic nitrogen ledger. Building both wheel
and source archive, `twine check` and installation are distinct checks.

## Still requires the human researcher/account owner

1. Confirm paper authors/contributions, affiliations, optional ORCID and funding.
   Existing citation metadata names Ram Yash; no additional identities are inferred.
2. Review RELATED_WORK.md and decide the scholarly contribution/build-versus-
   contribute justification. The draft contains no novelty or external-impact claim.
3. Supply legally reusable measured datasets and the independent novice study;
   these remain separate scientific/usability acceptance requirements.
4. Authenticate the intended PyPI/TestPyPI account and confirm project ownership
   or a configured trusted publisher. No secret is requested in chat. Build
   readiness does not establish the availability/ownership of a PyPI project name.
5. Future archive versions require review of version, creator, licence and exact
   files. The v0.8.1 manual deposit is complete; automatic GitHub-to-Zenodo
   archiving is NOT CONFIGURED. Do not create duplicate v0.8.1 records.
6. Review the final paper and decide whether/when to submit it. A draft is not a
   journal submission. Author/funding metadata and contribution review are incomplete.

If archival metadata exists from a real release, verify its version DOI and
concept DOI separately. Do not construct a DOI, insert a placeholder in the
schema, copy a dataset/paper DOI, or infer archiving from a GitHub tag alone.
An optional `.zenodo.json` is deliberately absent to avoid overriding CITATION.cff
with divergent metadata.

## Primary process documentation read

- [PyPA packaging tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
  and [strict distribution README check](https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/).
- [JOSS paper format](https://joss.readthedocs.io/en/latest/paper.html): current
  required content includes research impact, state of the field and AI disclosure.
- [Zenodo repository enablement](https://help.zenodo.org/docs/github/enable-repository/),
  [GitHub release archiving](https://help.zenodo.org/docs/github/archive-software/github-upload/)
  and [citation metadata](https://help.zenodo.org/docs/github/describe-software/citation-file/).
- [MkDocs deployment](https://www.mkdocs.org/user-guide/deploying-your-docs/)
  and [GitHub custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
