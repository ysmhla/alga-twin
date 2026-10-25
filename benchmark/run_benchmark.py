"""Run the benchmark from a source checkout using Python 3.12+."""

import sys

if sys.version_info < (3, 12):
    raise SystemExit(
        "The benchmark toolchain (PEtab 0.9) requires Python 3.12+. Core AlgaTwin still supports 3.11."
    )

from alga_twin.benchmark.run import main

if __name__ == "__main__":
    raise SystemExit(main())
