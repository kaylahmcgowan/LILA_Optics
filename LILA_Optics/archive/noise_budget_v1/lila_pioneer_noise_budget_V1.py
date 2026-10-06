#!/usr/bin/env python3
"""Exploratory displacement-noise budget for the LILA-Pioneer strainmeter.

The model separates published LILA terms from literature-transferred alternatives,
assumption-based scenarios, and diagnostic upper limits.  It is intentionally easy
to edit: all numerical assumptions live in the ``LILAParameters`` dataclass.

Primary references
------------------
Creighton et al., "Fundamental Noise and Gravitational-Wave Sensitivity of the
Laser Interferometer Lunar Antenna (LILA)", arXiv:2508.18437.
Jani et al., "Laser Interferometer Lunar Antenna (LILA): Advancing the U.S.
Priorities in Gravitational-wave and Lunar Science", arXiv:2508.11631.
Camp et al., JOSA A 17, 120 (2000), DOI: 10.1364/JOSAA.17.000120.

This is a concept model, not a final instrument requirement or measured budget.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Physical constants (SI)
HBAR = 1.054_571_817e-34
C = 299_792_458.0
KB = 1.380_649e-23


@dataclass
class LILAParameters:
    # Published LILA-Pioneer design assumptions
    arm_length_m: float = 5_000.0
    opening_angle_deg: float = 90.0
    wavelength_m: float = 1_064e-9
    temperature_K: float = 300.0
    effective_detected_power_W: float = 0.500  # eta * P

    # Published LILA thermal PSD normalizations at 1 Hz
    thermal_target_psd_1Hz_m2_per_Hz: float = 1.2e-33
    thermal_conservative_psd_1Hz_m2_per_Hz: float = 6.0e-32

    # Published lunar-dust scattering model
    dust_psd_reference_m2_per_Hz: float = 1.6e-35
    dust_density_per_m3: float = 3.0e-3
    dust_radius_m: float = 0.7e-6
    dust_speed_m_per_s: float = 300.0
    arm_beam_radius_m: float = 1.0e-2

    # Published laser-frequency allocation; actual spectrum is not yet supplied
    laser_frequency_asd_Hz_per_rtHz: float = 3.0e-10

    # Assumed fused-silica substrate for a lower-level Brownian estimate
    substrate_poisson_ratio: float = 0.17
    substrate_youngs_modulus_Pa: float = 72.0e9
    substrate_loss_angle: float = 1.0e-7
    narrowest_beam_radius_m: float = 0.5e-3

    # Exploratory laser RIN -> phase conversion scenario
    rin_asd_1Hz_per_rtHz: float = 2.0e-6
    rin_low_frequency_corner_Hz: float = 0.10
    amplitude_to_phase_rad_per_rin: float = 1.0e-4

    # Exploratory pointing scenario: 2 * spot offset * angular jitter
    beam_spot_offset_m: float = 0.10e-3
    angular_jitter_asd_1Hz_rad_per_rtHz: float = 1.0e-12
    angular_jitter_corner_Hz: float = 0.10

    # Exploratory local bench thermoelastic scenario
    local_unbalanced_path_m: float = 0.10
    bench_effective_cte_per_K: float = 1.0e-8
    temperature_asd_1Hz_K_per_rtHz: float = 1.0e-7
    temperature_spectrum_power: float = 1.0  # ASD proportional to f^-power

    # Exploratory electronics/phasemeter floor
    electronics_phase_asd_rad_per_rtHz: float = 3.0e-10

    # Apollo instrument-floor-derived seismic diagnostic, not measured background
    apollo_acceleration_floor_m_per_s2_rtHz: float = 1.0e-10
    seismic_valid_min_Hz: float = 0.05
    seismic_valid_max_Hz: float = 2.0
    assumed_differential_seismic_coupling: float = 1.0e-2

    # Frequency grid
    frequency_min_Hz: float = 1.0e-3
    frequency_max_Hz: float = 10.0
    frequency_points: int = 1600


CURVE_STATUS = {
    "thermal_target": "Published LILA target; design estimate, not measured",
    "thermal_conservative": "Published LILA conservative alternative; not added to target total",
    "shot": "Published formula evaluated at the LILA target effective detected power",
    "dust": "Published LILA estimate using LADEE-informed dust parameters",
    "laser_frequency": "Published allocation projected to length; flat spectrum assumed",
    "substrate_brownian": "Assumption-based fused-silica substrate calculation",
    "rin": "Assumption-based amplitude-to-phase conversion",
    "pointing": "Assumption-based spot-offset and angular-jitter coupling",
    "bench_thermoelastic": "Assumption-based local path, CTE, and temperature spectrum",
    "electronics": "Assumption-based flat phasemeter phase floor",
    "seismic_absolute_ceiling": "Apollo instrument-floor-derived absolute displacement diagnostic",
    "seismic_differential_scenario": "Assumed fraction of diagnostic absolute motion; not a coherence model",
}


def _rss(*amplitude_spectra: np.ndarray) -> np.ndarray:
    """Root-sum-square uncorrelated amplitude spectral densities."""
    return np.sqrt(np.sum([np.square(x) for x in amplitude_spectra], axis=0))


def frequency_grid(p: LILAParameters) -> np.ndarray:
    return np.logspace(
        np.log10(p.frequency_min_Hz),
        np.log10(p.frequency_max_Hz),
        p.frequency_points,
    )


def calculate_noise_curves(
    f: np.ndarray, p: LILAParameters
) -> Dict[str, np.ndarray]:
    """Return equivalent differential-displacement ASDs in m/sqrt(Hz)."""
    nu0 = C / p.wavelength_m

    thermal_target = np.sqrt(
        p.thermal_target_psd_1Hz_m2_per_Hz
        * (p.temperature_K / 300.0)
        / f
    )
    thermal_conservative = np.sqrt(
        p.thermal_conservative_psd_1Hz_m2_per_Hz
        * (p.temperature_K / 300.0)
        / f
    )

    shot = np.full_like(
        f,
        np.sqrt(
            HBAR
            * C
            * p.wavelength_m
            / (2.0 * np.pi * p.effective_detected_power_W)
        ),
    )

    dust_psd = (
        p.dust_psd_reference_m2_per_Hz
        * (p.arm_length_m / 5_000.0)
        * (p.dust_density_per_m3 / 3.0e-3)
        * (p.dust_radius_m / 0.7e-6) ** 6
        * (p.dust_speed_m_per_s / 300.0) ** -1
        * (p.arm_beam_radius_m / 1.0e-2) ** -1
    )
    dust = np.full_like(f, np.sqrt(dust_psd))

    # A one-arm frequency-to-range coupling: dx = L * dnu / nu.
    laser_frequency = np.full_like(
        f,
        p.arm_length_m * p.laser_frequency_asd_Hz_per_rtHz / nu0,
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
            * p.narrowest_beam_radius_m
            * p.substrate_youngs_modulus_Pa
        )
    )

    rin_asd = p.rin_asd_1Hz_per_rtHz * np.sqrt(
        1.0 + (p.rin_low_frequency_corner_Hz / f) ** 2
    )
    rin = (
        p.wavelength_m
        / (4.0 * np.pi)
        * p.amplitude_to_phase_rad_per_rin
        * rin_asd
    )

    angular_jitter = p.angular_jitter_asd_1Hz_rad_per_rtHz * np.sqrt(
        1.0 + (p.angular_jitter_corner_Hz / f) ** 2
    )
    pointing = 2.0 * p.beam_spot_offset_m * angular_jitter

    temperature_asd = p.temperature_asd_1Hz_K_per_rtHz * f ** (
        -p.temperature_spectrum_power
    )
    bench_thermoelastic = (
        p.local_unbalanced_path_m
        * p.bench_effective_cte_per_K
        * temperature_asd
    )

    electronics = np.full_like(
        f,
        p.wavelength_m
        / (4.0 * np.pi)
        * p.electronics_phase_asd_rad_per_rtHz,
    )

    seismic_absolute_ceiling = np.full_like(f, np.nan)
    valid = (f >= p.seismic_valid_min_Hz) & (f <= p.seismic_valid_max_Hz)
    seismic_absolute_ceiling[valid] = (
        p.apollo_acceleration_floor_m_per_s2_rtHz
        / (2.0 * np.pi * f[valid]) ** 2
    )
    seismic_differential_scenario = (
        p.assumed_differential_seismic_coupling * seismic_absolute_ceiling
    )

    baseline_total = _rss(thermal_target, shot, dust)
    estimated_total = _rss(
        thermal_target,
        shot,
        dust,
        laser_frequency,
        substrate_brownian,
        rin,
        pointing,
        bench_thermoelastic,
        electronics,
    )

    return {
        "thermal_target": thermal_target,
        "thermal_conservative": thermal_conservative,
        "shot": shot,
        "dust": dust,
        "laser_frequency": laser_frequency,
        "substrate_brownian": substrate_brownian,
        "rin": rin,
        "pointing": pointing,
        "bench_thermoelastic": bench_thermoelastic,
        "electronics": electronics,
        "seismic_absolute_ceiling": seismic_absolute_ceiling,
        "seismic_differential_scenario": seismic_differential_scenario,
        "baseline_total": baseline_total,
        "estimated_total": estimated_total,
    }


def curves_dataframe(
    f: np.ndarray, curves: Dict[str, np.ndarray]
) -> pd.DataFrame:
    data = {"frequency_Hz": f}
    data.update({f"{name}_m_per_rtHz": values for name, values in curves.items()})
    return pd.DataFrame(data)


def reference_table(
    f: np.ndarray,
    curves: Dict[str, np.ndarray],
    reference_frequencies: Iterable[float] = (1e-3, 1e-2, 1e-1, 1.0, 10.0),
) -> pd.DataFrame:
    names = [
        "thermal_target",
        "thermal_conservative",
        "shot",
        "dust",
        "laser_frequency",
        "rin",
        "pointing",
        "bench_thermoelastic",
        "electronics",
        "baseline_total",
        "estimated_total",
    ]
    rows = []
    for freq in reference_frequencies:
        row = {"frequency_Hz": float(freq)}
        row.update(
            {
                name: float(np.interp(np.log(freq), np.log(f), curves[name]))
                for name in names
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).set_index("frequency_Hz")


def assumptions_table(p: LILAParameters) -> pd.DataFrame:
    published = {
        "arm_length_m",
        "opening_angle_deg",
        "wavelength_m",
        "temperature_K",
        "effective_detected_power_W",
        "thermal_target_psd_1Hz_m2_per_Hz",
        "thermal_conservative_psd_1Hz_m2_per_Hz",
        "dust_psd_reference_m2_per_Hz",
        "dust_density_per_m3",
        "dust_radius_m",
        "dust_speed_m_per_s",
        "arm_beam_radius_m",
        "laser_frequency_asd_Hz_per_rtHz",
    }
    rows = []
    for name, value in asdict(p).items():
        rows.append(
            {
                "parameter": name,
                "value": value,
                "status": "Published LILA input" if name in published else "Editable assumption",
            }
        )
    return pd.DataFrame(rows)


def plot_noise_budget(
    f: np.ndarray,
    curves: Dict[str, np.ndarray],
    output_path: str | Path | None = None,
) -> plt.Figure:
    """Plot confidence through line weight, opacity, and line style."""
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "legend.fontsize": 8.5,
            "font.family": "DejaVu Sans",
        }
    )
    fig, (ax, ax_env) = plt.subplots(
        2,
        1,
        figsize=(14.5, 9.5),
        sharex=True,
        gridspec_kw={"height_ratios": [1.45, 1.0], "hspace": 0.14},
    )

    # Dark solid: directly specified/evaluated from the LILA paper.
    ax.loglog(
        f,
        curves["thermal_target"],
        color="#9B3D1F",
        lw=2.5,
        label="Thermal Brownian — LILA target (published)",
    )
    ax.loglog(
        f,
        curves["shot"],
        color="#174A6E",
        lw=2.5,
        label="Shot noise — 500 mW effective detected power (published)",
    )
    ax.loglog(
        f,
        curves["dust"],
        color="#356B4B",
        lw=2.2,
        label="Lunar dust scattering (published estimate)",
    )

    # Pale solid: published alternative, but less directly tied to the proposed hardware.
    ax.loglog(
        f,
        curves["thermal_conservative"],
        color="#D9A38D",
        lw=2.0,
        alpha=0.62,
        label="Thermal Brownian — conservative alternative",
    )

    # Dashed: explicit assumptions or an allocation without an actual spectrum.
    assumed_styles = [
        ("laser_frequency", "Laser frequency allocation (flat assumed)", "#6F5A8A", 0.78),
        ("substrate_brownian", "Substrate Brownian (assumed fused silica)", "#B89052", 0.58),
        ("rin", "RIN → phase coupling scenario", "#8E80A7", 0.58),
        ("pointing", "Beam pointing scenario", "#A89BB9", 0.52),
        ("bench_thermoelastic", "Local bench thermoelastic scenario", "#C9907D", 0.55),
        ("electronics", "Electronics phase floor scenario", "#6E91A4", 0.58),
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
        curves["baseline_total"],
        color="#111111",
        lw=3.1,
        label="Baseline total: published target terms",
        zorder=10,
    )
    ax.loglog(
        f,
        curves["estimated_total"],
        color="#666666",
        lw=2.2,
        ls="--",
        label="Exploratory total: baseline + assumed terms",
        zorder=9,
    )
    ax.set_ylabel(r"Equivalent displacement ASD  [m/$\sqrt{\mathrm{Hz}}$]")
    ax.set_title("LILA-Pioneer exploratory noise budget")
    ax.text(
        0.012,
        0.025,
        "Dark solid = published LILA model   •   Pale solid = published alternative\n"
        "Dashed = assumption-based estimate; edit parameters before treating as a requirement",
        transform=ax.transAxes,
        fontsize=9,
        color="#333333",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#CCCCCC", "alpha": 0.92},
    )
    ax.grid(True, which="major", alpha=0.24)
    ax.grid(True, which="minor", alpha=0.08)
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        borderaxespad=0.0,
        ncol=1,
        frameon=True,
        framealpha=0.94,
    )

    # Environmental diagnostic panel.  The absolute curve is intentionally not
    # included in either total because it is an Apollo instrument floor, not a
    # measured differential LILA noise spectrum.
    ax_env.loglog(
        f,
        curves["baseline_total"],
        color="#111111",
        lw=2.4,
        label="Published-target baseline total (reference)",
    )
    ax_env.loglog(
        f,
        curves["seismic_absolute_ceiling"],
        color="#BBC2CA",
        lw=2.0,
        ls=":",
        label="Apollo instrument-floor-derived absolute displacement",
    )
    ax_env.loglog(
        f,
        curves["seismic_differential_scenario"],
        color="#9FA9B4",
        lw=2.0,
        ls="--",
        label="Illustrative 1% differential seismic coupling",
    )
    ax_env.loglog(
        f,
        curves["bench_thermoelastic"],
        color="#C9907D",
        lw=1.7,
        ls="--",
        alpha=0.60,
        label="Local bench thermoelastic scenario",
    )
    ax_env.set_xlabel("Frequency [Hz]")
    ax_env.set_ylabel(r"Displacement ASD  [m/$\sqrt{\mathrm{Hz}}$]")
    ax_env.set_title("Environmental diagnostics and high-uncertainty scenarios", loc="left", fontsize=11.5)
    ax_env.grid(True, which="major", alpha=0.24)
    ax_env.grid(True, which="minor", alpha=0.08)
    ax_env.legend(loc="lower left", frameon=True, framealpha=0.94)
    ax_env.text(
        0.99,
        0.04,
        "Seismic curves are not included in totals.\nA lunar differential PSD/coherence model is still required.",
        ha="right",
        va="bottom",
        transform=ax_env.transAxes,
        fontsize=9,
        color="#555555",
    )

    for axis in (ax, ax_env):
        axis.set_xlim(f.min(), f.max())
    ax.set_ylim(1e-21, 3e-13)
    ax_env.set_ylim(1e-18, 1e-7)
    fig.suptitle(
        "5 km single-arm strainmeter • 1064 nm • 300 K • no suspension or arm cavity",
        y=0.995,
        fontsize=10.5,
        color="#4A4A4A",
    )
    fig.subplots_adjust(right=0.72, top=0.93)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=220, bbox_inches="tight")
    return fig


LIMITATIONS = [
    "Published LILA curves are design estimates/allocations, not measured lunar instrument noise.",
    "The two LILA arms are modeled as independent single-arm strainmeters; Michelson common-mode laser-noise cancellation is not applied.",
    "The target thermal curve is an effective coating-dominated term. The conservative thermal curve is an alternative and is not added to it.",
    "The substrate Brownian curve assumes fused silica, a 0.5 mm beam radius, and a 1e-7 loss angle; actual substrates and beam sizes are not fixed.",
    "The 500 mW value is effective detected power (eta*P). A complete 5 km transmit/receive diffraction and optical-loss budget is still needed.",
    "Laser frequency noise is plotted as the paper's flat allocation. A stabilization-cavity and control-loop spectrum is not modeled.",
    "RIN coupling requires the final phase readout topology, fringe/heterodyne operating point, and measured amplitude-to-phase conversion.",
    "Beam pointing requires the optical geometry, wavefront curvature, spot offsets, alignment control, and angular-noise spectra.",
    "The bench thermoelastic term assumes a local unbalanced path, effective CTE, and temperature ASD; the thermal enclosure model is outstanding.",
    "The electronics curve is an assumed phase floor; photodiode, transimpedance, ADC, clock, oscillator, and digital control budgets are outstanding.",
    "The Apollo seismic number was an instrument noise floor near 0.5 Hz. Converting it to displacement does not produce a lunar background measurement.",
    "The illustrative 1% seismic differential coupling is not a spatial-coherence or lunar wave-propagation calculation.",
    "Moonquakes, thermal cracking, micrometeorite transients, lander activity, astronauts, and nearby infrastructure are not modeled.",
    "The dust calculation uses a single particle radius and speed and is frequency-independent; a size/velocity distribution would be more realistic.",
    "Noise sources are combined as uncorrelated. Correlations and control-loop reinjection are not included.",
    "This plot is displacement noise only. Conversion to strain must include the LILA geometry and frequency-dependent lunar normal-mode response.",
    "Suspension thermal noise, free-mass radiation-pressure noise, atmospheric/acoustic noise, and terrestrial residual-gas noise are intentionally omitted for LILA-Pioneer.",
]


def write_outputs(output_dir: str | Path = ".") -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    p = LILAParameters()
    f = frequency_grid(p)
    curves = calculate_noise_curves(f, p)

    paths = {
        "figure": output_dir / "lila_pioneer_noise_budget.png",
        "data": output_dir / "lila_pioneer_noise_budget_data.csv",
        "reference_table": output_dir / "lila_pioneer_reference_values.csv",
        "assumptions": output_dir / "lila_pioneer_model_assumptions.csv",
    }
    plot_noise_budget(f, curves, paths["figure"])
    plt.close("all")
    curves_dataframe(f, curves).to_csv(paths["data"], index=False)
    reference_table(f, curves).to_csv(paths["reference_table"])
    assumptions_table(p).to_csv(paths["assumptions"], index=False)
    return paths


if __name__ == "__main__":
    paths = write_outputs(Path(__file__).resolve().parent)
    for label, path in paths.items():
        print(f"{label}: {path}")
