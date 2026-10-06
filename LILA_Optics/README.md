# LILA Optics

iLILA optical modeling, analytic noise studies, figures and research updates.
Work snapshot: **1 October 2026**, Kaylah McGowan.

## Start here

- [1 km Fintrace runner](models/ilila_1km/run_ilila_1km.py) and [YAML](models/ilila_1km/ilila_1km.yaml)
- [Executed reference-noise and readout notebook](analysis/iLILA_Reference_Noise_and_Allowance.ipynb)
- [Weekly research slides](presentations/iLILA_Weekly_Research_Updates.pptx): October 1 update on slides 19–25
- [Project plan](docs/iLILA_Optical_Sensitivity_Project_Plan.docx)
- [Study parameters and meeting notes](docs/2026-10-01_parameters_and_status.md)
- [Current scientific plots](figures/current)

## Run the 1 km model

Activate the existing compatible **optical Fintrace / Finesse 3** environment:

```bash
python models/ilila_1km/run_ilila_1km.py --check-only
python models/ilila_1km/run_ilila_1km.py
```

The runner resolves its YAML relative to its own location. It writes to
`models/ilila_1km/ilila_1km_outputs/` by default. `--out PATH` changes that directory.
It produces outgoing beam-size, Gouy-phase and curvature plots for both transverse
planes of both arms, a gtrace layout, and `run_report.json`.

If an older environment specifically fails to import `AstigmaticLens`, the
explicit compatibility option is:

```bash
python models/ilila_1km/run_ilila_1km.py --legacy-lens-shim
```

The provided model contains no lenses. The alias is only an import workaround,
not validation of an astigmatic lens. `--skip-layout` skips gtrace rendering while
retaining Finesse propagation. Required optics dependencies and the relevant API
documentation are listed in the runner. Do not install an unrelated finance
package named Fintrace. Optical Fintrace installation instructions:
https://fintrace.readthedocs.io/en/latest/installation.html

**Status:** syntax, configuration and independent vacuum-propagation checks passed.
Full Fintrace execution remains pending. The 20 mm launch beam radius and optic
diameters are provisional. Each coordinate arm baseline is 1000 m. The plate
beamsplitter may produce unequal optical paths despite equal coordinate lengths.

## Run the analytic notebook

Open `analysis/iLILA_Reference_Noise_and_Allowance.ipynb` in Jupyter with NumPy,
pandas and matplotlib installed, then run its cells in order. The saved outputs
contain the executed September 24 calculations reviewed on October 1. Its relative
figure paths write to the notebook kernel's working directory. Committed snapshots
are in `figures/current/`, and the readout table is in `analysis/data/`.

The notebook contains the manuscript thermal/shot/dust baseline, additional-noise
allowances, laser-frequency mismatch ceilings and hypothetical readout comparisons.
It does not run Finesse and does not establish achieved instrument sensitivity.

## Scientific status and conventions

- Lunar baseline: 1 km, 1064 nm, 300 K, effective detected power eta P = 0.5 W.
- Preliminary flat displacement target: 1e-15 m/sqrt(Hz), 1–100 mHz.
- Optimistic reference at 1 mHz: 1.1003e-15 m/sqrt(Hz), before seismic and technical noise.
- The alternative 10% total-ASD envelope is illustrative, not an approved requirement.
- Frequency-noise ceilings that consume 100% of the extra PSD leave no allocation for other terms.
- The 1550 nm, 100 nW readout study is a separate idealized bench comparison.
- Seismic spectra/coherence, real detector and laser noise, lunar response and science SNR remain pending.
- A replacement readout shot-noise model must replace the reference shot term, not be added to it.

## Repository organization

| Directory | Contents |
|---|---|
| `models/ilila_1km/` | Current 1 km YAML and runner |
| `models/bench/` | Earlier Michelson runners and 1064/1550 nm bench configurations |
| `analysis/` | Current executed notebook and numerical readout table |
| `figures/current/` | Five current analysis figures |
| `figures/bench_archive/` | Earlier bench layout exports |
| `presentations/` | Current weekly deck and prior optical-model overview |
| `docs/` | Project plan, assumptions and status notes |
| `archive/` | Earlier V1/V2 noise models, data, plots and reports |
| `references/` | Supplied manuscript and APRA optical-layout source |

Older V1/V2 material remains historical. Its assumptions must not be treated as
validated measurements or silently substituted for the current baseline. Existing
root-level repository uploads are retained. Exact duplicate source uploads are
represented once in this export; `EXPORT_MANIFEST.json` records filename aliases
and SHA-256 checksums. Temporary renders, caches and unrelated projects are excluded.
