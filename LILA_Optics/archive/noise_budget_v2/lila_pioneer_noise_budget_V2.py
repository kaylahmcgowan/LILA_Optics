#!/usr/bin/env python3
"""Proposal-aligned exploratory technical noise budget for iLILA/LDC-IA.

The controlling configuration is taken from the August 2026 Templeton proposal:

* iLILA: 1 km equal-arm, dark-fringe, LIGO-like interferometric strainmeter.
* LDC-IA laboratory demonstrator: 1 m arms with emulated far reflectors.
* Science/verification band: 1-100 mHz.
* Preliminary displacement requirement: 1e-15 m/sqrt(Hz).
* 1064 nm, 1 W input laser amplified to 2 W, reference-cavity frequency
  stabilization, mode cleaners, and +/-10 mK optical-bench stability.

The proposal deliberately assigns WP I.C to close the technical noise budget.
Accordingly, only proposal-specified requirements and hardware parameters are
drawn dark. Curves requiring unprovided spectra or transfer functions remain
dashed and parameterized. Older 5 km LILA sensitivity-paper estimates are
retained only as pale "heritage" curves, rescaled where appropriate.

This is not a measured budget or a final requirement allocation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HBAR = 1.054_571_817e-34
C = 299_792_458.0
KB = 1.380_649e-23


@dataclass
class LILAParameters:
    # Directly specified in the current Templeton proposal
    arm_length_m: float = 1_000.0
    laboratory_arm_length_m: float = 1.0
    opening_angle_deg: float = 90.0
    wavelength_m: float = 1_064e-9
    input_laser_power_W: float = 1.0
    amplified_laser_power_W: float = 2.0
    target_frequency_min_Hz: float = 1.0e-3
    target_frequency_max_Hz: float = 1.0e-1
    displacement_requirement_m_per_rtHz: float = 1.0e-15
    optical_bench_temperature_stability_K: float = 10.0e-3
    lovbb_acceleration_asd_m_per_s2_rtHz: float = 1.0e-11
    lovbb_equivalent_displacement_m_per_rtHz: float = 1.0e-15
    far_reflector_diameter_m: float = 0.100
    far_reflector_alignment_tolerance_deg: float = 3.0
    temperature_K: float = 300.0  # room-temperature lab/proposal environment

    # Optical-link assumptions not yet provided by the proposal
    assumed_power_per_arm_W: float = 1.0
    assumed_round_trip_optical_efficiency: float = 0.05
    assumed_photodiode_quantum_efficiency: float = 0.80

    # Heritage LILA sensitivity-paper thermal alternatives (not current allocations)
    heritage_thermal_target_psd_1Hz_m2_per_Hz: float = 1.2e-33
    heritage_thermal_conservative_psd_1Hz_m2_per_Hz: float = 6.0e-32

    # Heritage lunar-dust estimate, rescaled from 5 km to the current arm length
    heritage_dust_psd_reference_m2_per_Hz: float = 1.6e-35
    dust_density_per_m3: float = 3.0e-3
    dust_radius_m: float = 0.7e-6
    dust_speed_m_per_s: float = 300.0
    assumed_arm_beam_radius_m: float = 1.0e-2

    # Assumed frequency-noise spectrum and equal-arm mismatch coupling
    assumed_arm_length_mismatch_m: float = 1.0e-2
    assumed_laser_frequency_asd_1Hz_Hz_per_rtHz: float = 1.0
    laser_frequency_corner_Hz: float = 1.0e-2

    # Assumed fused-silica substrate Brownian parameters
    substrate_poisson_ratio: float = 0.17
    substrate_youngs_modulus_Pa: float = 72.0e9
    substrate_loss_angle: float = 1.0e-7
    assumed_narrowest_beam_radius_m: float = 0.5e-3

    # Assumed RIN-to-phase coupling at the dark-fringe readout
    assumed_rin_asd_0p1Hz_per_rtHz: float = 2.0e-6
    rin_low_frequency_corner_Hz: float = 1.0e-2
    assumed_amplitude_to_phase_rad_per_rin: float = 1.0e-4

    # Assumed alignment/beam-pointing coupling
    assumed_beam_spot_offset_m: float = 0.10e-3
    assumed_angular_jitter_asd_0p1Hz_rad_per_rtHz: float = 1.0e-12
    angular_jitter_corner_Hz: float = 1.0e-2

    # Assumed local optical-bench thermoelastic spectrum.  The proposal's
    # +/-10 mK stability is a bound, not an ASD, so it is not used as one.
    assumed_local_unbalanced_path_m: float = 0.10
    assumed_bench_effective_cte_per_K: float = 1.0e-8
    assumed_temperature_asd_0p1Hz_K_per_rtHz: float = 1.0e-7
    temperature_asd_power: float = 1.0

    # Assumed photoreceiver/digitizer and actuator/control residuals
    assumed_readout_phase_floor_rad_per_rtHz: float = 1.0e-9
    assumed_actuator_residual_asd_0p1Hz_m_per_rtHz: float = 1.0e-16
    actuator_residual_corner_Hz: float = 1.0e-2

    # Assumed non-dust scattered-light displacement-equivalent floor
    assumed_scattered_light_asd_0p1Hz_m_per_rtHz: float = 1.0e-17
    scattered_light_corner_Hz: float = 1.0e-2

    # Environmental diagnostic assumptions
    apollo_instrument_floor_m_per_s2_rtHz: float = 1.0e-10
    apollo_diagnostic_min_Hz: float = 5.0e-2
    apollo_diagnostic_max_Hz: float = 1.0
    assumed_seismic_subtraction_residual_fraction: float = 0.10

    # Display grid
    frequency_min_Hz: float = 1.0e-4
    frequency_max_Hz: float = 1.0
    frequency_points: int = 1601


PROPOSAL_SPECIFIED_PARAMETERS = {
    "arm_length_m",
    "laboratory_arm_length_m",
    "opening_angle_deg",
    "wavelength_m",
    "input_laser_power_W",
    "amplified_laser_power_W",
    "target_frequency_min_Hz",
    "target_frequency_max_Hz",
    "displacement_requirement_m_per_rtHz",
    "optical_bench_temperature_stability_K",
    "lovbb_acceleration_asd_m_per_s2_rtHz",
    "lovbb_equivalent_displacement_m_per_rtHz",
    "far_reflector_diameter_m",
    "far_reflector_alignment_tolerance_deg",
}


CURVE_STATUS = {
    "requirement": "Current proposal: preliminary 1e-15 m/sqrt(Hz) requirement in 1-100 mHz",
    "heritage_thermal_target": "Older LILA sensitivity-paper coating-dominated target; not a current allocation",
    "heritage_thermal_conservative": "Older conservative optical/mount alternative; not added to totals",
    "shot": "Formula is fundamental; received power, return loss, and quantum efficiency are assumed",
    "heritage_dust": "Older LILA/LADEE estimate rescaled from 5 km to 1 km",
    "laser_frequency": "Assumed spectrum coupled through an assumed equal-arm mismatch",
    "substrate_brownian": "Assumed fused-silica substrate, loss angle, and beam radius",
    "rin": "Assumed RIN spectrum and amplitude-to-phase transfer coefficient",
    "pointing": "Assumed angular jitter and beam-spot offset",
    "bench_thermoelastic": "Assumed temperature ASD, unequal path, and effective CTE",
    "readout": "Assumed combined photoreceiver/digitizer phase floor",
    "actuator_control": "Assumed actuator and control-loop residual displacement",
    "scattered_light": "Assumed non-dust scattered-light displacement-equivalent floor",
    "lovbb_equivalent": "Current proposal approximation for the seismic reference in 1-100 mHz",
    "seismic_residual": "Illustrative residual after 10x subtraction; not a demonstrated subtraction curve",
    "apollo_absolute": "Apollo instrument-floor-derived absolute displacement diagnostic, not lunar background",
}


def _rss(*spectra: np.ndarray) -> np.ndarray:
    return np.sqrt(np.sum([np.square(x) for x in spectra], axis=0))


def _colored_power_law(
    f: np.ndarray, level: float, corner: float, power: float = 1.0
) -> np.ndarray:
    return level * np.sqrt(1.0 + (corner / f) ** (2.0 * power))


def frequency_grid(p: LILAParameters) -> np.ndarray:
    return np.logspace(
        np.log10(p.frequency_min_Hz),
        np.log10(p.frequency_max_Hz),
        p.frequency_points,
    )


def calculate_noise_curves(
    f: np.ndarray, p: LILAParameters
) -> Dict[str, np.ndarray]:
    """Calculate displacement ASDs in m/sqrt(Hz)."""
    nu0 = C / p.wavelength_m
    in_band = (f >= p.target_frequency_min_Hz) & (
        f <= p.target_frequency_max_Hz
    )

    requirement = np.full_like(f, np.nan)
    requirement[in_band] = p.displacement_requirement_m_per_rtHz

    heritage_thermal_target = np.sqrt(
        p.heritage_thermal_target_psd_1Hz_m2_per_Hz
        * (p.temperature_K / 300.0)
        / f
    )
    heritage_thermal_conservative = np.sqrt(
        p.heritage_thermal_conservative_psd_1Hz_m2_per_Hz
        * (p.temperature_K / 300.0)
        / f
    )

    effective_detected_power = (
        p.assumed_power_per_arm_W
        * p.assumed_round_trip_optical_efficiency
        * p.assumed_photodiode_quantum_efficiency
    )
    shot = np.full_like(
        f,
        np.sqrt(
            HBAR
            * C
            * p.wavelength_m
            / (2.0 * np.pi * effective_detected_power)
        ),
    )

    heritage_dust_psd = (
        p.heritage_dust_psd_reference_m2_per_Hz
        * (p.arm_length_m / 5_000.0)
        * (p.dust_density_per_m3 / 3.0e-3)
        * (p.dust_radius_m / 0.7e-6) ** 6
        * (p.dust_speed_m_per_s / 300.0) ** -1
        * (p.assumed_arm_beam_radius_m / 1.0e-2) ** -1
    )
    heritage_dust = np.full_like(f, np.sqrt(heritage_dust_psd))

    laser_frequency_asd = _colored_power_law(
        f,
        p.assumed_laser_frequency_asd_1Hz_Hz_per_rtHz,
        p.laser_frequency_corner_Hz,
    )
    # Equal-arm Michelson coupling: full arm length cancels to first order;
    # residual frequency noise couples through the macroscopic mismatch.
    laser_frequency = (
        p.assumed_arm_length_mismatch_m * laser_frequency_asd / nu0
    )

    substrate_brownian = np.sqrt(
        2.0
        * KB
        * p.temperature_K
        * (1.0 - p.substrate_poisson_ratio**2)
        * p.substrate_loss_angle
        / (
            np.pi ** 1.5
            * f
            * p.assumed_narrowest_beam_radius_m
            * p.substrate_youngs_modulus_Pa
        )
    )

    rin_asd = _colored_power_law(
        f,
        p.assumed_rin_asd_0p1Hz_per_rtHz,
        p.rin_low_frequency_corner_Hz,
    )
    rin = (
        p.wavelength_m
        / (4.0 * np.pi)
        * p.assumed_amplitude_to_phase_rad_per_rin
        * rin_asd
    )

    angular_jitter = _colored_power_law(
        f,
        p.assumed_angular_jitter_asd_0p1Hz_rad_per_rtHz,
        p.angular_jitter_corner_Hz,
    )
    pointing = 2.0 * p.assumed_beam_spot_offset_m * angular_jitter

    temperature_asd = p.assumed_temperature_asd_0p1Hz_K_per_rtHz * (
        f / 0.1
    ) ** (-p.temperature_asd_power)
    bench_thermoelastic = (
        p.assumed_local_unbalanced_path_m
        * p.assumed_bench_effective_cte_per_K
        * temperature_asd
    )

    readout = np.full_like(
        f,
        p.wavelength_m
        / (4.0 * np.pi)
        * p.assumed_readout_phase_floor_rad_per_rtHz,
    )

    actuator_control = _colored_power_law(
        f,
        p.assumed_actuator_residual_asd_0p1Hz_m_per_rtHz,
        p.actuator_residual_corner_Hz,
    )
    scattered_light = _colored_power_law(
        f,
        p.assumed_scattered_light_asd_0p1Hz_m_per_rtHz,
        p.scattered_light_corner_Hz,
    )

    lovbb_equivalent = np.full_like(f, np.nan)
    lovbb_equivalent[in_band] = p.lovbb_equivalent_displacement_m_per_rtHz
    seismic_residual = (
        p.assumed_seismic_subtraction_residual_fraction * lovbb_equivalent
    )

    apollo_absolute = np.full_like(f, np.nan)
    apollo_valid = (f >= p.apollo_diagnostic_min_Hz) & (
        f <= p.apollo_diagnostic_max_Hz
    )
    apollo_absolute[apollo_valid] = (
        p.apollo_instrument_floor_m_per_s2_rtHz
        / (2.0 * np.pi * f[apollo_valid]) ** 2
    )

    heritage_physical_floor = _rss(
        heritage_thermal_target,
        shot,
        heritage_dust,
        substrate_brownian,
    )
    provisional_instrument_total = _rss(
        heritage_thermal_target,
        shot,
        heritage_dust,
        laser_frequency,
        substrate_brownian,
        rin,
        pointing,
        bench_thermoelastic,
        readout,
        actuator_control,
        scattered_light,
    )

    return {
        "requirement": requirement,
        "heritage_thermal_target": heritage_thermal_target,
        "heritage_thermal_conservative": heritage_thermal_conservative,
        "shot": shot,
        "heritage_dust": heritage_dust,
        "laser_frequency": laser_frequency,
        "substrate_brownian": substrate_brownian,
        "rin": rin,
        "pointing": pointing,
        "bench_thermoelastic": bench_thermoelastic,
        "readout": readout,
        "actuator_control": actuator_control,
        "scattered_light": scattered_light,
        "lovbb_equivalent": lovbb_equivalent,
        "seismic_residual": seismic_residual,
        "apollo_absolute": apollo_absolute,
        "heritage_physical_floor": heritage_physical_floor,
        "provisional_instrument_total": provisional_instrument_total,
    }


def curves_dataframe(
    f: np.ndarray, curves: Dict[str, np.ndarray]
) -> pd.DataFrame:
    data = {"frequency_Hz": f}
    data.update({f"{key}_m_per_rtHz": value for key, value in curves.items()})
    return pd.DataFrame(data)


def reference_table(
    f: np.ndarray,
    curves: Dict[str, np.ndarray],
    reference_frequencies: Iterable[float] = (1e-3, 1e-2, 1e-1, 1.0),
) -> pd.DataFrame:
    keys = [
        "requirement",
        "heritage_thermal_target",
        "heritage_thermal_conservative",
        "shot",
        "heritage_dust",
        "laser_frequency",
        "rin",
        "pointing",
        "bench_thermoelastic",
        "readout",
        "actuator_control",
        "scattered_light",
        "heritage_physical_floor",
        "provisional_instrument_total",
        "lovbb_equivalent",
        "seismic_residual",
    ]
    rows = []
    for freq in reference_frequencies:
        row = {"frequency_Hz": float(freq)}
        for key in keys:
            value = np.interp(np.log(freq), np.log(f), curves[key])
            row[key] = float(value) if np.isfinite(value) else np.nan
        rows.append(row)
    return pd.DataFrame(rows).set_index("frequency_Hz")


def assumptions_table(p: LILAParameters) -> pd.DataFrame:
    rows = []
    for name, value in asdict(p).items():
        if name in PROPOSAL_SPECIFIED_PARAMETERS:
            status = "Current Templeton proposal"
        elif name.startswith("heritage_"):
            status = "Older LILA sensitivity-paper heritage"
        else:
            status = "Editable assumption/model control"
        rows.append({"parameter": name, "value": value, "status": status})
    return pd.DataFrame(rows)


def configuration_summary(p: LILAParameters) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "configuration": "LILA-AITD / LDC-IA laboratory demonstrator",
                "arm_length_m": p.laboratory_arm_length_m,
                "measurement": "Equal-arm dark-fringe interferometer with emulated far reflectors",
                "status": "Proposed TRL-4 laboratory maturation",
            },
            {
                "configuration": "iLILA",
                "arm_length_m": p.arm_length_m,
                "measurement": "Lunar Deformation Channel; equal-arm dark-fringe interferometer",
                "status": "Initial science-capable lunar strainmeter",
            },
            {
                "configuration": "LILA Observatory LDC",
                "arm_length_m": 40_000.0,
                "measurement": "Full-scale Lunar Deformation Channel",
                "status": "Future observatory; not modeled here",
            },
        ]
    )


def plot_noise_budget(
    f: np.ndarray,
    curves: Dict[str, np.ndarray],
    p: LILAParameters,
    output_path: str | Path | None = None,
) -> plt.Figure:
    """Plot proposal requirements, heritage curves, and dashed assumptions."""
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "legend.fontsize": 8.3,
            "font.family": "DejaVu Sans",
        }
    )
    fig, (ax, ax_env) = plt.subplots(
        2,
        1,
        figsize=(14.5, 9.5),
        sharex=True,
        gridspec_kw={"height_ratios": [1.45, 1.0], "hspace": 0.15},
    )

    for axis in (ax, ax_env):
        axis.axvspan(
            p.target_frequency_min_Hz,
            p.target_frequency_max_Hz,
            color="#E8EDF2",
            alpha=0.55,
            zorder=0,
        )

    # Dark: proposal-controlled requirement.
    ax.loglog(
        f,
        curves["requirement"],
        color="#111111",
        lw=3.0,
        label="Preliminary iLILA requirement (current proposal)",
        zorder=12,
    )

    # Pale solid: older sensitivity-paper estimates retained for traceability.
    ax.loglog(
        f,
        curves["heritage_thermal_target"],
        color="#A64B2A",
        lw=2.1,
        alpha=0.72,
        label="Thermal Brownian target (heritage estimate)",
    )
    ax.loglog(
        f,
        curves["heritage_thermal_conservative"],
        color="#E1B8A5",
        lw=1.9,
        alpha=0.62,
        label="Thermal Brownian conservative alternative (heritage)",
    )
    ax.loglog(
        f,
        curves["heritage_dust"],
        color="#78A087",
        lw=1.8,
        alpha=0.65,
        label="Dust scattering rescaled to 1 km (heritage estimate)",
    )

    # Dashed: current architecture, but spectra/transfer inputs are assumptions.
    assumed_styles = [
        ("shot", "Shot noise (assumed 5% round-trip efficiency)", "#205B82", 0.82),
        ("laser_frequency", "Laser frequency via assumed 1 cm arm mismatch", "#6F5A8A", 0.72),
        ("substrate_brownian", "Substrate Brownian (assumed fused silica)", "#B89052", 0.55),
        ("rin", "RIN -> phase coupling scenario", "#8E80A7", 0.55),
        ("pointing", "Alignment/beam-pointing scenario", "#AAA0BA", 0.50),
        ("bench_thermoelastic", "Optical-bench thermoelastic scenario", "#C9907D", 0.58),
        ("readout", "Photoreceiver + digitizer phase-floor scenario", "#6E91A4", 0.58),
        ("actuator_control", "Actuator/control residual scenario", "#A87B72", 0.54),
        ("scattered_light", "Non-dust optical-scatter scenario", "#7E9A91", 0.48),
    ]
    for key, label, color, alpha in assumed_styles:
        ax.loglog(
            f,
            curves[key],
            color=color,
            lw=1.55,
            ls="--",
            alpha=alpha,
            label=label,
        )

    ax.loglog(
        f,
        curves["heritage_physical_floor"],
        color="#555555",
        lw=2.2,
        alpha=0.72,
        label="Heritage physical floor (thermal + shot + substrate + dust)",
        zorder=10,
    )
    ax.loglog(
        f,
        curves["provisional_instrument_total"],
        color="#303030",
        lw=2.7,
        ls="--",
        label="Provisional total including assumption-based terms",
        zorder=11,
    )
    ax.set_ylabel(r"Equivalent differential displacement ASD  [m/$\sqrt{\mathrm{Hz}}$]")
    ax.set_title("iLILA / LDC-IA proposal-aligned technical noise model")
    ax.grid(True, which="major", alpha=0.24)
    ax.grid(True, which="minor", alpha=0.08)
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        borderaxespad=0.0,
        frameon=True,
        framealpha=0.95,
    )
    ax.text(
        0.012,
        0.025,
        "Dark solid = current proposal requirement   |   Pale solid = older LILA heritage\n"
        "Dashed = explicit assumption; not yet a requirement or measured spectrum",
        transform=ax.transAxes,
        fontsize=9,
        color="#333333",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#CCCCCC", "alpha": 0.92},
    )

    # Environmental/reference panel.
    ax_env.loglog(
        f,
        curves["requirement"],
        color="#111111",
        lw=2.5,
        label="iLILA displacement requirement",
        zorder=8,
    )
    ax_env.loglog(
        f,
        curves["lovbb_equivalent"],
        color="#2F6947",
        lw=2.5,
        label="LOVBB equivalent displacement (proposal approximation)",
    )
    ax_env.loglog(
        f,
        curves["seismic_residual"],
        color="#86A894",
        lw=2.0,
        ls="--",
        label="Illustrative residual after 10x seismic subtraction",
    )
    ax_env.loglog(
        f,
        curves["apollo_absolute"],
        color="#BBC2CA",
        lw=2.0,
        ls=":",
        label="Apollo instrument-floor-derived absolute displacement",
    )
    ax_env.loglog(
        f,
        curves["bench_thermoelastic"],
        color="#C9907D",
        lw=1.7,
        ls="--",
        alpha=0.60,
        label="Optical-bench thermoelastic scenario",
    )
    ax_env.set_xlabel("Frequency [Hz]")
    ax_env.set_ylabel(r"Displacement ASD  [m/$\sqrt{\mathrm{Hz}}$]")
    ax_env.set_title(
        "Environmental reference and disturbance-removal scenarios",
        loc="left",
        fontsize=11.5,
    )
    ax_env.grid(True, which="major", alpha=0.24)
    ax_env.grid(True, which="minor", alpha=0.08)
    ax_env.legend(loc="lower left", frameon=True, framealpha=0.95)
    ax_env.text(
        0.99,
        0.04,
        "The Apollo curve is not a measured lunar background.\n"
        "The subtraction curve is a scenario, not demonstrated performance.",
        ha="right",
        va="bottom",
        transform=ax_env.transAxes,
        fontsize=9,
        color="#555555",
    )

    for axis in (ax, ax_env):
        axis.set_xlim(f.min(), f.max())
    ax.set_ylim(1e-21, 3e-12)
    ax_env.set_ylim(1e-18, 3e-8)
    fig.suptitle(
        "Current proposal: 1 km equal-arm dark-fringe interferometer | 1-100 mHz | 1e-15 m/sqrt(Hz)",
        y=0.985,
        fontsize=10.5,
        color="#4A4A4A",
    )
    fig.subplots_adjust(right=0.70, top=0.93)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=220, bbox_inches="tight")
    return fig


LIMITATIONS = [
    "The controlling proposal defines the technical noise budget as future WP I.C work; most curves therefore remain provisional allocations or assumptions.",
    "The proposal's preliminary requirement is 1e-15 m/sqrt(Hz) in 1-100 mHz for 1 km iLILA arms; the 1 m laboratory system must demonstrate equivalent displacement sensitivity and transfer-function fidelity, not astrophysical strain reach.",
    "The current architecture is an equal-arm, dark-fringe, LIGO-like interferometer. Laser frequency noise is coupled through assumed residual arm mismatch rather than the full 1 km arm length.",
    "The proposal specifies a 1 W laser amplified to 2 W but not received photodiode power. Shot noise assumes 1 W per arm, 5% round-trip optical efficiency, and 80% quantum efficiency.",
    "A Gaussian propagation/link budget for the 1 km path and 100 mm MoonLIGHT corner cube is outstanding; diffraction, clipping, CCR response, and pointing losses may change received power substantially.",
    "The older LILA thermal curves are retained only as heritage. The current proposal does not allocate coating, substrate, mount, actuator, and bench Brownian noise separately.",
    "The substrate Brownian curve assumes fused silica, a 0.5 mm narrowest beam radius, and a 1e-7 loss angle; final materials and beam sizes are not specified.",
    "The proposal's +/-10 mK bench stability is not a spectral density. The thermoelastic curve assumes a temperature ASD, unequal local path, and effective CTE that must be replaced by a thermal-control transfer model.",
    "Laser frequency noise assumes a 1 Hz/sqrt(Hz) level, 10 mHz corner, and 1 cm arm mismatch. The reference cavity, mode-cleaner, and control-loop spectra are not modeled.",
    "RIN coupling requires the actual dark-fringe offset/contrast defect, photodetection topology, and measured amplitude-to-phase coefficient.",
    "Alignment noise requires transmitted/returned beam geometry, wavefront curvature, MoonLIGHT CCR coupling, spot offsets, actuator spectra, and alignment-control transfer functions.",
    "Photoreceiver/digitizer noise is represented by a flat assumed phase floor. Photocurrent, transimpedance, dark current, Johnson noise, ADC noise, clock noise, dynamic range, and timing jitter are outstanding.",
    "Actuator/control residual and non-dust scattered-light curves are placeholders pending the ISI-CT/ISI-DG designs and measured transfer functions.",
    "The heritage dust curve uses a single particle radius and speed and simple 1 km rescaling; a particle distribution and optical-scattering geometry are needed.",
    "Radiation damage, stray electric/magnetic fields, thermal surface deformation, support-structure coupling, lander/rover activity, moonquakes, and meteoroid transients are tracked but not assigned spectra.",
    "The proposal quotes LOVBB acceleration performance and an approximate 1e-15 m/sqrt(Hz) strainmeter-equivalent displacement. A full sensor response, spatial coherence, and subtraction-transfer model is still required.",
    "The Apollo diagnostic is an instrument floor, not a continuous lunar seismic-background measurement.",
    "The 10% seismic residual is an illustrative 10x subtraction scenario and is not demonstrated performance or a proposal requirement.",
    "All instrument terms are combined as uncorrelated. Correlations, control-loop reinjection, nonstationarity, lines, and transient glitches are excluded.",
    "The plot is displacement noise. Conversion to astrophysical strain must apply the iLILA geometry and the frequency-dependent lunar normal-mode transfer function; simple division by 1 km omits lunar resonant amplification.",
    "Suspension thermal noise and free-mass radiation-pressure noise are omitted for iLILA's fixed Lunar Deformation Channel; they return for the future suspended Geodesic Displacement Channel.",
]


def write_outputs(output_dir: str | Path = ".") -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    p = LILAParameters()
    f = frequency_grid(p)
    curves = calculate_noise_curves(f, p)
    paths = {
        "figure": output_dir / "lila_pioneer_noise_budget_V2.png",
        "data": output_dir / "lila_pioneer_noise_budget_data_V2.csv",
        "reference_table": output_dir / "lila_pioneer_reference_values_V2.csv",
        "assumptions": output_dir / "lila_pioneer_model_assumptions_V2.csv",
    }
    plot_noise_budget(f, curves, p, paths["figure"])
    plt.close("all")
    curves_dataframe(f, curves).to_csv(paths["data"], index=False)
    reference_table(f, curves).to_csv(paths["reference_table"])
    assumptions_table(p).to_csv(paths["assumptions"], index=False)
    return paths


if __name__ == "__main__":
    outputs = write_outputs(Path(__file__).resolve().parent)
    for label, path in outputs.items():
        print(f"{label}: {path}")
