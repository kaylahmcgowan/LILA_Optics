# Parameters and status for the October 1, 2026 update

The lunar baseline and the bench readout comparison use distinct parameter sets.
They are not yet one integrated instrument prediction.

| Study | Parameters and assumptions |
|---|---|
| Thermal, shot and dust reference | 1 km arms; 1064 nm; 300 K; effective eta P = 0.5 W; optimistic thermal term, with the conservative term as an alternative; independent PSD addition |
| Dust term | Number density 3e-3 m^-3; particle radius 0.7 micrometers; speed 300 m/s; manuscript beam-width parameter w = 1 cm |
| Additional noise | Flat target 1e-15 m/sqrt(Hz), 1–100 mHz; separately, illustrative 10% increase in total ASD; allowance shared across omitted independent terms |
| Laser frequency | Ideal vacuum Michelson; 1064 nm; mismatch 1 mm, 1 cm, 10 cm, 1 m; 10% ASD envelope; 100% of extra PSD assigned to laser frequency as an upper ceiling |
| Readouts | Main example 1550 nm, 100 nW total returning power before efficiency, eta=0.8, additional LO=100 nW; direct at quadrature, balanced homodyne at dark, single-tone real-quadrature heterodyne at dark; ideal detectors and perfect visibility |
| Prepared Fintrace model | 1000 m coordinate baseline per arm; 1064 nm; 1 W launch normalization; 20 mm input 1/e^2 intensity radius; waist 0.75 m before BS; flat end mirrors; 150 mm mirror diameter; 200 mm BS diameter; BS thickness 5 mm, n=1.45; no cavities |

## Findings

The optimistic reference totals 1.1003e-15 m/sqrt(Hz) at 1 mHz, about 10% above
the preliminary target. Its flat-target crossing is about 1.213 mHz. A 10% total
ASD increase permits additional ASD of 0.4583 times the reference for all omitted
independent noise together.

At 10 mHz, the illustrative envelope allows a 1 cm mismatch at 1064 nm to tolerate
about 4.67 Hz/sqrt(Hz) of frequency noise when that term consumes the whole extra
PSD. This is a conditional ceiling, not a measured laser spectrum.

At the hypothetical 1550 nm / 100 nW / 80% efficiency setting, direct quadrature
and the specified heterodyne give 3.12e-13 m/sqrt(Hz) of ideal shot noise.
Balanced homodyne at dark gives 2.21e-13 m/sqrt(Hz). The advantage is relative to
single-port direct detection at quadrature; an ideal direct readout approaching
dark reaches the same limiting shot ASD but has zero linear gain at exact dark.
All three calibrated readouts retain the same ideal arm-mismatch frequency coupling.

## What is complete

The analytic notebook is executed. The plots, parameter comparisons, project plan
and weekly update slides are available. The Fintrace script and YAML are prepared
and passed configuration and independent analytic checks; a full run is pending.

## What remains

Run the 1 km Fintrace model, then validate readout displacement and frequency gains
in Finesse. Obtain actual detector and laser spectra and a consistent returned-power
definition. Reconcile the dust beam-width convention with the provisional Fintrace
beam. Specify seismic input/coherence/support response, and obtain numerical lunar
mode data before calculating strain sensitivity and explicit science SNR cases.

No lunar seismic amplitude or suppression factor has been assigned. The 0.5 W
effective detected power is not a confirmed launch-power requirement. The 100 nW
readout example is not an APRA measurement or an APD410C performance specification.
