# LILA-Pioneer exploratory noise-budget model

This package models equivalent differential-displacement amplitude spectral density (ASD) for the proposed 5 km LILA-Pioneer lunar strainmeter. It is a transparent concept model: published LILA equations are separated from transferred literature estimates, explicit assumptions, and diagnostic upper limits.

## Files

- `LILA_Pioneer_Noise_Budget.ipynb`: guided notebook for changing assumptions and rerunning the budget.
- `lila_pioneer_noise_budget.py`: reusable model and plotting functions.
- `lila_pioneer_noise_budget.png`: default two-panel noise-budget figure.
- `lila_pioneer_noise_budget_data.csv`: all default curves on the full frequency grid.
- `lila_pioneer_reference_values.csv`: selected values at 1 mHz, 10 mHz, 0.1 Hz, 1 Hz, and 10 Hz.
- `lila_pioneer_model_assumptions.csv`: parameter values labeled as published inputs or editable assumptions.

## Confidence encoding

- **Dark solid curves:** directly specified or evaluated from the LILA fundamental-noise paper.
- **Pale solid curves:** published alternatives that are less directly tied to the final proposed hardware.
- **Dashed curves:** assumption-based estimates or allocations without an actual measured spectrum.
- **Dotted curves:** diagnostic ceilings that must not be interpreted as measured LILA differential noise.

The black solid total combines only the published LILA target thermal, shot, and dust terms. The gray dashed total adds the assumption-based laser-frequency, substrate, RIN, pointing, bench-thermal, and electronics scenarios. The conservative thermal curve is an alternative case and is not double-counted. Seismic diagnostic curves are excluded from both totals.

## Default LILA-Pioneer configuration

- Two independent single-arm strainmeters in a right-angle L configuration
- 5 km baseline
- 1064 nm laser
- 300 K
- 500 mW effective detected power (`eta * P`)
- Fixed, unsuspended optics
- No high-gain arm cavity

## Implemented published terms

### Effective thermal Brownian noise

The target and conservative alternatives follow

`Sx(f) = Sx(1 Hz) * (T / 300 K) * (f / 1 Hz)^-1`,

with `Sx(1 Hz) = 1.2e-33 m^2/Hz` for the coating-dominated target and `6.0e-32 m^2/Hz` for the conservative optical/mount estimate.

### Shot noise

`Sx = hbar * c * lambda / (2 * pi * eta * P)`.

At `eta * P = 500 mW`, the default ASD is approximately `1.04e-16 m/sqrt(Hz)`.

### Lunar dust scattering

The LILA estimate is normalized to `1.6e-35 m^2/Hz` for a 5 km arm, dust density `3e-3 m^-3`, particle radius `0.7 micrometers`, speed `300 m/s`, and 1 cm beam radius. The strong sixth-power dependence on particle radius is preserved.

### Laser-frequency allocation

For one arm, the model uses `dx = L * dnu / nu`. The paper's `dnu = 3e-10 Hz/sqrt(Hz)` is plotted as a flat allocation because an actual stabilization spectrum is not yet available.

## Assumption-based terms

The default exploratory curves include:

- Fused-silica substrate Brownian noise using the fluctuation-dissipation formula
- Laser RIN converted to phase with an editable amplitude-to-phase coefficient
- Angular jitter coupled through an assumed beam-spot offset
- Local optical-bench thermoelastic drift from an assumed path imbalance, CTE, and temperature ASD
- A flat electronics/phasemeter phase floor
- A 1% differential seismic-coupling illustration

These curves are deliberately dashed. Their default numbers are placeholders selected to make the missing transfer functions visible, not claimed LILA requirements.

## Seismic warning

The LILA paper cites an Apollo seismometer instrumental acceleration floor just above `1e-10 m/s^2/sqrt(Hz)` near 0.5 Hz. The model converts that number to an absolute displacement diagnostic using `x = a / (2*pi*f)^2` only over 0.05–2 Hz. This is not a measurement of the continuous lunar background, and an assumed percentage of it is not a physical 5 km differential-coherence model. Replace it with a lunar ground-motion PSD plus a spatial transfer/coherence calculation before using it in a total noise budget.

## Highest-priority improvements

1. Produce a complete transmit/receive optical link budget to replace the assumed 500 mW effective detected power.
2. Specify the ranging/readout topology and derive laser frequency, RIN, oscillator, electronics, and control-loop transfer functions for a single-arm strainmeter.
3. Specify substrate, coating stack, mount/actuator, beam sizes, and bench materials; then calculate Brownian and thermo-optic terms separately or by finite-element modeling.
4. Model the thermal enclosure and local unequal optical paths through the lunar day/night cycle.
5. Obtain or construct a lunar seismic background PSD and 5 km spatial coherence model; treat moonquakes and human/lander activity separately as transients or veto categories.
6. Add beam propagation, diffraction, wavefront curvature, pointing-control, and scattered-light geometry.
7. Add measured photodiode, transimpedance, ADC, clock, oscillator, and digital-control noise.
8. Convert displacement noise to strain only after applying the LILA geometry and frequency-dependent lunar normal-mode response.

## Important omissions

Suspension thermal noise, free-mass radiation-pressure noise, atmospheric/acoustic noise, and terrestrial residual-gas noise are intentionally omitted for the fixed, unsuspended LILA-Pioneer concept. Noise sources are currently combined as uncorrelated.

## References

- [Creighton et al., LILA fundamental noise and sensitivity](https://arxiv.org/abs/2508.18437)
- [Jani et al., LILA white paper](https://arxiv.org/abs/2508.11631)
- [Camp et al., early LIGO light-noise analysis](https://doi.org/10.1364/JOSAA.17.000120)
- [Harry, coating thermal-noise formulas](https://dcc.ligo.org/LIGO-T0900161/public)
- [Gras et al., coating thermal-noise measurement](https://doi.org/10.1103/PhysRevD.95.022001)
