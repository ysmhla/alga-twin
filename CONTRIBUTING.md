# Contributing to AlgaTwin

Scientific accuracy comes first. Please make changes as small, testable pull requests, with a clear explanation of physical assumptions and units.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e '.[dev]'
pytest -q
```

Before introducing a new growth model, include (1) equations and units, (2) parameter definitions, (3) physical boundary tests, (4) at least one transparent verification dataset or synthetic parameter-recovery case, and (5) a limitations section.

Do not commit proprietary datasets or confidential experimental records. A model fit is not an independent prediction benchmark. Cite empirical parameter sources and license permissions for any contributed data.
