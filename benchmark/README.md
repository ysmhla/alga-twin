# AlgaTwin benchmark pipeline — v0.6.0

The shipped dataset is **SYNTHETIC**, with three runs, 48 measurements and a
seeded generator. It is a software check, not cultivation evidence for
C. minutissima. No measured dataset has been supplied. No article data have
been downloaded, fabricated as empirical observations or digitised.

Licence: the synthetic fixture uses the repository **MIT** licence, copied into
its directory with attribution and a SHA-256 digest. Each accepted future
dataset must carry its own explicit licence record and permission-text evidence.

## Run the actual pipeline

The benchmark toolchain requires **Python 3.12+** because PEtab 0.9.0 requires it.
Core AlgaTwin retains Python 3.11 support. From the repository root:

    python3.12 -m pip install -r requirements.txt -e '.[dev,benchmark]'
    python3.12 benchmark/run_benchmark.py --registry benchmark/registry.json --output /tmp/alga-benchmark

Use a new/empty output directory. The script never silently overwrites a previous
run. `--scoreboard path.md` explicitly selects an additional scoreboard output.
`benchmark/scoreboard.md` and `benchmark/results/synthetic_v0_6/` contain the
actual checked synthetic run, not prospective scores. Package versions and the registry hash are in the output environment record.
No runtime-performance claim is made.

Regenerate the source synthetic fixture deliberately with:

    python3.12 benchmark/generate_synthetic.py

This rewrites only `benchmark/datasets/synthetic_batch/`. It uses
`alga_twin.calibration_io.synthetic_job`, seed 619 and UNVERIFIED/DEMO biological
assumptions. The source model is Monod with saturation light; the default
benchmark estimates its shared growth-rate parameter. All generated measurement
rows retain origin in metadata. Negative additive assay errors are not clipped.

## Metadata schema and loaders

`metadata.schema.json` is a JSON Schema 2020-12 document. Required fields:

| Field | Required interpretation |
|---|---|
| species | Actual dataset species; SYNTHETIC for the artificial fixture |
| reactor | Description of the batch reactor/geometry |
| light | Constant/diurnal mode, photon-flux unit and value for every run |
| path | Optical path unit and value for every run |
| N_source | Actual feed compound/available N description; no nitrate-ion/N ambiguity |
| units, basis | Canonical state/time/light/path units; DW biomass and elemental N |
| licence | Identifier, URL, attribution, review status/reviewer/date, redistribution flag |
| DOI, doi_status | Provided DOI remains UNVERIFIED; absent unpublished DOI is NOT_ASSIGNED; synthetic DOI is null/NOT_APPLICABLE_SYNTHETIC |
| files | Relative job/observation/permission-text paths, each with SHA-256 |
| origin, source | SYNTHETIC/MEASURED and source/generation description |

`load_dataset(metadata_path,schema_path)` checks schema, units/bases, condition
agreement, source/model species consistency, origin and file hashes before fitting.
It rejects missing/unreviewed licences, a false redistribution flag, empty
permission evidence, stale hashes, absolute/escaping/symlink-out paths, missing
species inputs and carbon/nitrate-ion substitutions. No carbon fraction is
assumed. Input observations use the Step 3 long CSV/job schema.

For measured data, `CHECKED_BY_DATA_PROVIDER` records the provider's permission
review. The loader verifies that the required record and matching evidence file
exist; it does not authenticate ownership or issue a legal opinion. A populated
DOI field or a paper's open-access status is not automatic permission to reuse
its datasets. The software does not mark source metadata VERIFIED from a DOI
regex. No source numeric value is promoted to a preset.

## PEtab export and interoperability boundary

Each accepted problem is exported as **PEtab 2.0.0** YAML plus parameter,
observable, measurement, condition and experiment TSV files. Model language is
`alga_twin_native_v1`: a versioned JSON definition interpreted by the existing
AlgaTwin model code. Physical units, evidence records, starting states, controlled
conditions, technical replicate ids and noise law are retained. No alternate
optical quadrature or reduced surrogate is substituted.

`load_petab(problem.yaml)` supplies an implementation of libpetab's public Model
interface to its public Problem constructor, runs the official PEtab validators,
and rebuilds the likelihood from the exported tables. It does not secretly load
a duplicate original calibration job. Round-trip tests compare likelihoods,
units, dark limits and nitrogen ledgers across Monod/Droop and the light options.
The PEtab reader repeats the permission and metadata-unit checks as well as
SHA-256 checks. Regenerate from reviewed inputs after an
intentional edit. Native artifacts require their recorded AlgaTwin version.

**Compatibility limit:** libpetab 0.9's default `Problem.from_yaml` model factory
supports SBML/PySB/BNGL, not this native language. Use our explicit reader. Generic
SBML/AMICI import, standalone SBML export and all arbitrary PEtab features are
NOT IMPLEMENTED. The supported subset has one native model, one initial period
per run, direct state observables, numeric condition overrides and one fixed
additive/log-normal error family. General priors, expressions and event sequences
are not silently interpreted. This is PEtab 2 native-model exchange, not a claim
of universal simulator compatibility.

## Optimization, profiles and whole-run holdouts

The script reads the exported PEtab problem, then executes both:

1. **AlgaTwin:** the established SciPy joint-fit/profile refusal gate and
   leave-one-whole-run-out refitting/reprofiling. These results determine the
   reported conditional estimates and held-out metrics.
2. **pyPESTO 0.7.0:** real Powell optimization and `parameter_profile` on the
   same exported likelihood, using deterministic initial/0.25/0.75-coordinate
   starts and full-bound profiles at 0.1 coordinate steps. Its full-data optimum
   is compared with the native one (NLL tolerance 1e-3 + 1e-6*abs(native NLL)).

Search coordinates decode the explicit linear/log bounds in the job. PEtab 2
parameters/bounds remain in physical units; `algaTwinSearchScale` is an optional
algorithm annotation, not a prior or a literature range. Powell success uses
SciPy status 0; finite objective values alone are not convergence evidence.
Failed external profiles or materially different optima refuse the benchmark
result. Raw external best parameter vectors are not exported to bypass the
native NOT IDENTIFIABLE gate. Profile grids remain diagnostic, labelled grids.

pyPESTO is a **full-data external cross-check** here; fold inference uses the
AlgaTwin engine. It is not falsely labelled pyPESTO CV or an independent dataset.
All intervals retain the Step 3 method/conditional assumptions. Optional MCMC,
empirical coverage calibration and a structural-identifiability proof are absent.

## Scoreboard and stored evidence

Every dataset has an explicit licence line, including refused entries. Rows
separate full-data in-sample RMSE from held-out RMSE. RMSE is pooled within each
observable using its measurement count and keeps its unit; biomass/N errors are
never merged into a unitless score. Fold-training metrics are also exported.
Held-out aggregation is withheld if any fold is unsupported; scored/total fold
counts and refusal reasons remain visible. Failed problems receive no score.
No model-ranking or novelty claim is made.

Each output includes environment/package versions, registry hash, the PEtab
bundle, metadata/permission evidence, native/pyPESTO profile CSVs, an evidence
JSON, separate metric/fold tables and held-out predictions. Errors are not
imputed as zero. The main scoreboard is an engineering artifact: measured
out-of-sample evaluation remains pending licensed human-supplied data.

## Sources actually checked

- Official [PEtab 2.0 specification](https://petab.readthedocs.io/en/latest/v2/documentation_data_format.html): model-format independence, TSV/YAML structure, noise distributions and parameters.
- Installed **petab 0.9.0** public Model/Problem interfaces, default model factory and validators were inspected and executed.
- Official [pyPESTO profiling documentation](https://pypesto.readthedocs.io/en/v0.7.0/api/pypesto.profile.html) and installed **pyPESTO 0.7.0** optimizer/profile code were checked; actual calls are exercised, not mocked.

See ../docs/VERIFICATION.md for executed test/CI evidence and its limits.
