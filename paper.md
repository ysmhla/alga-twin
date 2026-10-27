---
title: 'AlgaTwin: evidence-aware microalgal batch simulation and conditional calibration'
tags:
  - Python
  - microalgae
  - photobioreactor
  - parameter estimation
authors:
  - name: Ram Yash
    affiliation: 1
affiliations:
  - name: Industrial University of Ho Chi Minh City, VT
    index: 1
date: 27 October 2026
bibliography: paper.bib
---

> DRAFT — NOT SUBMITTED. Author identity follows the existing CITATION.cff;
> current affiliation and no-funding declaration were supplied by the author on
> 27 October 2026. Authorship/contributions, optional ORCID and final related-work
> assessment still require human confirmation. The released v0.8.1 software is archived at
> https://doi.org/10.5281/zenodo.23665342. This is a
> reviewable JOSS-style draft, not a submission-ready or accepted paper.

# Summary

AlgaTwin is a Python research prototype for simulating the growth of a batch
microalgal culture and fitting selected model parameters to repeated cultivation
runs. Its intended users are laboratory researchers who need to connect biomass,
nitrogen and reactor-light measurements to a transparent mathematical model.
A Streamlit interface provides explicit unit mapping, a guided fitting workflow,
parameter-source tables and downloadable reports. The Python interface exposes
model equations, parameter records and ordered states independently of the UI.

The current research focus is *Chlorella minutissima*. The software does not
supply a complete species preset when the literature audit lacks the required
parameters. Missing extinction coefficients and carbon-to-dry-weight conversion
remain unset. A separate, deliberately selected teaching mode supplies artificial
inputs and data labelled SYNTHETIC, UNVERIFIED and DEMO. These fixtures exercise
software behaviour; they are not observations of this species.

# Statement of need

Batch cultivation analysis requires decisions about mass basis, light response,
nitrogen limitation and measurement noise. Treating a value reported for another
species, or per gram of carbon, as a dry-weight parameter can obscure those
choices. Likewise, a fitted curve alone does not establish that the data
separate its parameters or predict a new cultivation run. AlgaTwin records these
assumptions alongside the calculation and refuses some unsupported results.

The intended workflow is to upload measurements, map their columns, verify
units and replicate identities, supply a complete model configuration, fit
shared parameters and interpret the result with its limitations. A matched
OD/cell-count-to-dry-weight helper supports explicit linear or quadratic
calibration and refuses extrapolation. This conversion does not currently
propagate its uncertainty into growth-model intervals. The workflow is a
prototype: independent novice completion time and five observed human usability
issues have not yet been measured.

# State of the field

General tools already address these modelling tasks. pyFOOMB provides a
programmatic framework for bioprocess models [@pyfoomb]. pyPESTO exposes
parameter-estimation and diagnostic methods [@pypesto]. PEtab specifies
parameter-estimation problems across conditions [@petab]. NLoed provides
nonlinear experimental-design tools based on expected Fisher information
[@nloed]. AlgaTwin neither introduces these mathematical principles nor claims
to replace the broader capabilities of these projects. Its optional benchmark
pipeline uses actual pyPESTO profiles and PEtab 2 native-model validation.

PEtab Select already offers model-space search and AIC/AICc/BIC criteria with
external calibration [@petabselect]. An algal comparator, the REALM raceway model,
is described by its authors as a MATLAB mechanistic simulator coupling biological,
engineering and thermal processes with weather inputs [@realm]. Its source archive
has not been executed here; the retrieved licence field was unavailable and no
code, data or parameters were copied. These documentation comparisons establish
relevant prior work, not head-to-head performance or biological validation.

The present implementation explores a narrow microalgal workflow with explicit
species-evidence gaps, units, fit refusals and reports. A related-work table is
provided in `docs/RELATED_WORK.md`, but the human researcher has not checked it.
Consequently a definitive build-versus-contribute justification, unique scholarly
contribution or novelty claim remains unresolved. Further comparison may favour
contributing interfaces or application examples to an existing framework.

# Software design

A common model interface supports Monod nitrogen limitation and a reduced Droop
quota model, with selectable saturation, Haldane or steady-state Han light
responses. Optional cardinal-temperature and diurnal-light factors remain
conditional on explicitly supplied inputs. A separate removed-nitrogen ledger
checks dissolved, stored and removed nitrogen consistency. The reduced model
omits dynamic oxygen, carbon dioxide, pH, hydrodynamics and photoadaptation;
source equations, units and adaptations are documented in `docs/MODEL.md`.

Parameter records retain value, source, status, species, conditions, mass basis
and evidence tier. Source-reported points are not converted into invented
ranges. Fitted values remain unverified for source transcription. This separation
allows the numerical engine to run a declared teaching problem without silently
promoting its assumptions into literature evidence.

Calibration shares selected parameters across runs while retaining each run's
forcing and initial conditions. Additive or log-normal errors require explicit
fixed noise scales. Technical measurements retain distinct identities; culture
replicates use different run identifiers. Reoptimized profile likelihoods gate
parameter estimates and named conditional marginal intervals. Flat or open
profiles withhold estimates. Whole-run cross-validation refits and rechecks
profiles using training runs only, with held-out errors reported separately.

Model comparison uses identical data and noise with AIC/BIC, profile gates and
an explicitly approximate fixed-noise residual screen. Supplied decision windows
and fixed initial quota are conditioning assumptions. Experiment planning ranks
explicit proposed runs using local Fisher information at a supported fit and
shows the top three with reasons. Its local SD/volume ratios are not confidence
intervals, guarantees or a global optimum. A flat current profile, stale fit or
ill-conditioned information matrix refuses this local calculation.

# Research impact statement

Available evidence is reproducible engineering material: synthetic recovery and
failure cases, limiting-case and unit checks, nitrogen conservation, a
licence-bearing benchmark, executed tutorial notebooks and actual hosted-app
smoke exports. A known-best synthetic experiment is checked against independent
exponential-growth sensitivity algebra. Verification records identify actual
executed checks and their source commits rather than prospective pass claims.

No independent cultivation dataset, external adoption study, enabled scholarly
publication, calibrated interval coverage or measured research impact is
established. These materials support evaluation of the prototype's numerical
behaviour and transparency, not biological prediction accuracy. Licensed
measured benchmarks, an independent novice study and a reviewed related-work
assessment are required before stronger research-use or publication claims.

# Limitations

All inference conditions on the supplied model, fixed parameters, initial states,
noise and search bounds. Nonlinear profile and residual approximations can be
unreliable with scarce data; numerical screens are not structural-identifiability
proofs. Cultivation random effects, censoring, correlated errors, posterior
sampling and prediction uncertainty are not implemented. Proposed experiments
require researcher-supplied feasibility and budgets. No streaming state estimator
or hardware control is implemented, and the name “twin” does not establish an
online connection to a real reactor. Missing evidence stays visible rather than
being replaced by cross-species parameters or fabricated datasets.

# AI usage disclosure

OpenAI Codex, in a GPT-6-based session (precise model build identifier unavailable),
assisted with code, tests, source-audit documentation and this paper draft.
Quality checks include source reading, executable unit/limiting/conservation
checks, synthetic inference failures, linting and hosted-app smoke inspection.
They do not substitute for independent biological evidence or author review.
The author supplied the current affiliation and no-funding declaration.
The human researcher must still confirm scientific interpretation, authorship,
contributions, related work and the final submission text.

# Acknowledgements

The author reports no funding for this work. Additional contributors have not
been supplied; no unsupported acknowledgement is made.

# References
