# iLILA / LDC-IA proposal-aligned technical noise model

This model has been revised to follow the current August 2026 Templeton proposal, *Laser Interferometer Lunar Antenna (LILA): Listening for the First Cosmic Sound*. The proposal is the controlling design source; earlier LILA white-paper and sensitivity-paper values are retained only as clearly labeled heritage estimates.

## What changed from the earlier model

| Item | Earlier assumption | Current controlling proposal |
|---|---|---|
| Initial lunar instrument | 5 km pair of independent single-arm strainmeters | 1 km equal-arm, dark-fringe, LIGO-like interferometer |
| Laboratory system | Not modeled separately | 1 m LDC-IA demonstrator with emulated far reflectors |
| Primary band | Broad mHz-to-Hz concept band | 1–100 mHz verification/science band |
| Primary target | Heritage thermal/shot sensitivity | Preliminary displacement requirement of `1e-15 m/sqrt(Hz)` |
| Laser | 500 mW effective detected-power assumption | 1064 nm, 1 W input amplified to 2 W; received power unspecified |
| Frequency-noise coupling | Full-arm single-strainmeter coupling | Residual equal-arm mismatch coupling |
| Readout | Independent ranging channels | Returned beams recombine destructively at a dark fringe |
| Far reflectors | Generic mirror or metasurface | 100 mm MoonLIGHT corner-cube retroreflectors with MPAc pointing/control |
| Seismic treatment | Apollo-derived scenario only | LOVBB seismic reference plus subtraction/validation architecture |

## Controlling proposal parameters

- iLILA arm length: 1 km
- LDC-IA laboratory arm length: 1 m
- Equal-arm dark-fringe interferometric readout
- 1064 nm input laser
- 1 W laser amplified to 2 W before conditioning and splitting
- Reference cavity and frequency-stabilizer cavity
- Input/output mode-cleaning architecture
- Preliminary displacement requirement: `1e-15 m/sqrt(Hz)`
- Target band: 1–100 mHz
- Optical-bench stability: ±10 mK
- LOVBB target acceleration ASD: `1e-11 m/s^2/sqrt(Hz)`
- Proposal-stated LOVBB strainmeter-equivalent displacement: approximately `1e-15 m/sqrt(Hz)` in band
- 100 mm MoonLIGHT corner-cube far reflectors; alignment within approximately 3 degrees across 1 km

## Confidence encoding

- **Dark solid:** current proposal requirement or directly specified performance.
- **Pale solid:** older LILA sensitivity-paper estimate retained for traceability.
- **Dashed:** explicit assumption where the current proposal does not provide a spectrum or transfer function.
- **Dotted:** diagnostic ceiling that must not be interpreted as measured lunar background.

The shaded region marks the 1–100 mHz target band. The provisional instrument total is dashed because it necessarily combines unclosed assumptions. Seismic-reference and environmental diagnostic curves are not included in that total.

## Implemented instrument terms

### Preliminary displacement requirement

The current proposal uses `1e-15 m/sqrt(Hz)` over 1–100 mHz as the initial LDC-IA/iLILA requirement pending refinement by the Science Traceability Matrix and WP I.C Technical Noise Budget and Closure Plan.

### Heritage thermal estimates

The older LILA sensitivity paper supplies coating-dominated target and conservative optical/mount alternatives proportional to `f^-1/2` in ASD. They remain useful scale references, but the proposal does not adopt them as closed component allocations.

### Shot-noise scenario

The proposal specifies 2 W after amplification but not the received photodiode power after the 1 km round trip. The default scenario assumes:

- 1 W transmitted per arm after splitting
- 5% total round-trip optical efficiency
- 80% photodiode quantum efficiency

The model then evaluates

`Sx = hbar * c * lambda / (2*pi*eta*P_received)`.

These values are editable and the curve is dashed.

### Equal-arm laser-frequency coupling

Because the current proposal recombines two nominally equal arms at a dark fringe, common laser phase noise cancels to first order. Residual frequency noise is modeled as

`dx_frequency = delta_L_arm * dnu / nu0`,

where the arm mismatch and stabilized frequency-noise spectrum are assumptions. The default mismatch is 1 cm. This replaces the earlier and incorrect full-1-km coupling for the current topology.

### Technical-noise scenarios

Editable dashed terms include:

- Laser RIN converted to phase through an assumed amplitude-to-phase coefficient
- Alignment/beam pointing through an assumed beam-spot offset and angular-jitter ASD
- Optical-bench thermoelastic drift through an assumed temperature ASD, unequal local path, and effective CTE
- Combined photoreceiver and digitizer phase floor
- Actuator/control residual displacement
- Non-dust optical scattering

These correspond to the proposal's explicit instrument-noise and environmental-coupling categories, but the proposal intentionally leaves their measured spectra and closure criteria to WP I.C and Activity II.

## Seismic interpretation

The current proposal uses LOVBB as a seismic reference rather than treating every local ground motion as irreducible strainmeter noise. It specifies a target acceleration ASD of `1e-11 m/s^2/sqrt(Hz)` and states this corresponds approximately to `1e-15 m/sqrt(Hz)` differential displacement on the strainmeter in the 1–100 mHz band.

The model shows:

- The proposal-stated LOVBB-equivalent displacement
- An illustrative 10% residual after 10x subtraction
- The older Apollo instrument-floor-derived absolute displacement diagnostic

The 10% residual is not demonstrated performance or a formal requirement. The Apollo value is not a lunar background measurement. A final budget needs lunar ground-motion PSDs, spatial coherence over 1 km, LOVBB response, subtraction transfer functions, and false-alarm/false-dismissal tests.

## Highest-priority closure work

1. **1 km optical link budget:** Gaussian propagation, transmit beam, 100 mm CCR aperture, diffraction, clipping, CCR response, pointing losses, return efficiency, and effective detected power.
2. **Frequency stabilization:** reference-cavity noise, mode-cleaner response, control-loop gain, residual arm mismatch, oscillator/clock terms, and the 1–100 mHz spectrum.
3. **Thermal budget:** convert ±10 mK stability into a frequency-dependent thermal model; specify bench, substrate, coating, mounts, actuators, CTEs, loss angles, beam sizes, and temperature sensors.
4. **Readout budget:** photodiode responsivity, received photocurrent, dark current, shot current, transimpedance, Johnson noise, ADC quantization, clock jitter, linearity, and dynamic range.
5. **Alignment budget:** outgoing/return beam geometry, wavefront curvature, MoonLIGHT CCR/MPAc coupling, jitter spectra, spot offsets, alignment sensing, and control residuals.
6. **Disturbance separation:** lunar seismic PSD and coherence, LOVBB transfer function, subtraction gain, signal-injection tests, false alarms, and subtraction bias.
7. **Environmental spectra:** dust distribution, optical scatter, radiation-induced drift, electrostatic/stray-field effects, thermally driven lunar deformation, support coupling, lander/rover activity, moonquakes, and meteoroid impacts.
8. **Lunar response:** keep instrument displacement noise separate from the frequency-dependent lunar normal-mode response when converting to astrophysical strain.

## Files

- `LILA_Pioneer_Noise_Budget_V2.ipynb`: guided V2 notebook
- `lila_pioneer_noise_budget_V2.py`: reusable V2 model and plot functions
- `lila_pioneer_noise_budget_V2.png`: proposal-aligned V2 figure
- `lila_pioneer_noise_budget_data_V2.csv`: full V2 frequency-grid curves
- `lila_pioneer_reference_values_V2.csv`: V2 values at 1 mHz, 10 mHz, 100 mHz, and 1 Hz
- `lila_pioneer_model_assumptions_V2.csv`: V2 proposal parameters, heritage inputs, and editable assumptions

## Source hierarchy

1. Controlling source: *Laser Interferometer Lunar Antenna (LILA): Listening for the First Cosmic Sound*, Templeton proposal, August 2026.
2. [Creighton et al., LILA fundamental noise and sensitivity](https://arxiv.org/abs/2508.18437)
3. [Jani et al., LILA white paper](https://arxiv.org/abs/2508.11631)
4. [Camp et al., early LIGO light-noise analysis](https://doi.org/10.1364/JOSAA.17.000120)
5. [Harry, coating thermal-noise formulas](https://dcc.ligo.org/LIGO-T0900161/public)
