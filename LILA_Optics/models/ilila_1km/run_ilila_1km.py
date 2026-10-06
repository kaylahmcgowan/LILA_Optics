#!/usr/bin/env python3
"""Build the Fintrace 1 km Michelson and plot both outgoing arm beams.

Put this script beside ilila_1km.yaml, activate your existing optics environment:
    python run_ilila_1km.py
    python run_ilila_1km.py --check-only
    python run_ilila_1km.py --skip-layout

Requires the optical Fintrace package (mactodd315/fintrace), Finesse 3,
cosmicexplorer, gtrace, matplotlib and PyYAML in a compatible environment.
Check-only needs PyYAML and the Python standard library, not Fintrace.

Uses Fintrace to construct the optical model, then its inherited Finesse
propagate_beam method to plot each transverse plane separately. This avoids
Fintrace's version-dependent plot_beam_trace wrapper and tuple unpacking.
API references (checked 2026-10-01):
https://fintrace.readthedocs.io/en/latest/autoapi/fintrace/model/index.html
https://finesse.ifosim.org/docs/latest/api/finesse.model.html
https://finesse.ifosim.org/docs/latest/api/finesse.solutions.beamtrace.html

Scope: outgoing Gaussian propagation and layout, not sensitivity or SNR.
Flat mirrors are placeholders; return overlap/readout needs separate modeling.
End-to-end Fintrace execution was unavailable in the file-authoring environment.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys


def load_config(path):
    import yaml
    with path.open(encoding="utf-8") as stream:
        cfg = yaml.safe_load(stream)
    if not isinstance(cfg, dict):
        raise ValueError("YAML root must be an optical-component mapping.")
    expected = {"Laser": "Laser", "BS": "Beamsplitter", "MX": "Mirror",
                "MY": "Mirror", "PDAS": "Photodiode", "PDREFL": "Photodiode"}
    if set(cfg) != set(expected):
        raise ValueError("This runner expects the supplied six-component topology.")
    for name, kind in expected.items():
        if cfg[name].get("Type") != kind:
            raise ValueError(f"{name} must have Type: {kind}.")
        for axis in ("X", "Y"):
            if not math.isfinite(float(cfg[name]["Position"][axis])):
                raise ValueError(f"Nonfinite position: {name}.{axis}")
    connections = {
        "Laser": {"Front": "BS"},
        "BS": {"Front1": "Laser", "Front2": "MY", "Back1": "MX", "Back2": None},
        "MX": {"Front": "BS", "Back": None},
        "MY": {"Front": "BS", "Back": None},
    }
    for name, links in connections.items():
        if cfg[name].get("Connections") != links:
            raise ValueError(f"Unexpected connections on {name}; update the trace paths too.")
    for key in ("P", "Wavelength", "w"):
        value = float(cfg["Laser"][key])
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"Laser.{key} must be finite and positive.")
    roc = float(cfg["Laser"]["RoC"])
    if math.isnan(roc) or roc == 0:
        raise ValueError("Laser.RoC must be nonzero or .inf.")
    for name in ("BS", "MX", "MY"):
        optic = cfg[name]
        diameter = float(optic["diameter"])
        transmission, loss = float(optic["T"]), float(optic["L"])
        if not math.isfinite(diameter) or diameter <= 0:
            raise ValueError(f"Invalid diameter on {name}.")
        if not 0 <= transmission <= 1 or not 0 <= loss <= 1-transmission:
            raise ValueError(f"Invalid T/L on {name}.")
    return cfg


def xy(component):
    return tuple(float(component["Position"][a]) for a in ("X", "Y"))


def check_geometry(cfg):
    bx, by = xy(cfg["BS"])
    lx, ly = xy(cfg["Laser"])
    xx, yy = xy(cfg["MX"])
    yx, yy2 = xy(cfg["MY"])
    if not (math.isclose(ly, by, abs_tol=1e-9) and lx < bx and
            math.isclose(yy, by, abs_tol=1e-9) and xx > bx and
            math.isclose(yx, bx, abs_tol=1e-9) and yy2 > by):
        raise ValueError("Expected laser west, MX east and MY north of BS.")
    return {"input_m": math.dist(xy(cfg["Laser"]), xy(cfg["BS"])),
            "X_arm_coordinate_m": math.dist(xy(cfg["MX"]), xy(cfg["BS"])),
            "Y_arm_coordinate_m": math.dist(xy(cfg["MY"]), xy(cfg["BS"]))}


def analytic_check(cfg, lengths):
    """Independent free-space comparison only; excludes the BS substrate."""
    laser = cfg["Laser"]
    wave, w, roc = (float(laser[k]) for k in ("Wavelength", "w", "RoC"))
    q0 = 1 / complex(0 if math.isinf(roc) else 1/roc, -wave/(math.pi*w*w))
    rows = []
    for arm in ("X", "Y"):
        z = lengths["input_m"] + lengths[f"{arm}_arm_coordinate_m"]
        q = q0 + z
        radius = math.sqrt(-wave/(math.pi*(1/q).imag))
        gouy = math.degrees(math.atan2(q.real, q.imag)-math.atan2(q0.real, q0.imag))
        rows.append({"arm": arm, "vacuum_distance_m": z,
                     "vacuum_end_radius_m": radius, "vacuum_gouy_deg": gouy})
    return q0, {"label": "Analytic vacuum benchmark, excludes substrate",
                "rayleigh_range_m": q0.imag,
                "waist_distance_from_laser_m": -q0.real, "arms": rows}


def versions():
    result = {"python": sys.version.split()[0]}
    for package in ("fintrace", "finesse", "cosmicexplorer", "gtrace", "matplotlib", "PyYAML"):
        try:
            result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result[package] = "no distribution metadata"
    return result


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--yaml", type=Path, default=here/"ilila_1km.yaml")
    parser.add_argument("--out", type=Path, default=here/"ilila_1km_outputs")
    parser.add_argument("--check-only", action="store_true", help="Validate YAML and print a vacuum analytic benchmark.")
    parser.add_argument("--skip-layout", action="store_true", help="Skip gtrace rendering; still build and propagate the Finesse model.")
    parser.add_argument("--legacy-lens-shim", action="store_true", help="Opt in to the old AstigmaticLens import workaround. No lenses are allowed in this model.")
    args = parser.parse_args()
    cfg = load_config(args.yaml)
    lengths = check_geometry(cfg)
    q0, analytic = analytic_check(cfg, lengths)
    print(json.dumps({"coordinate_lengths": lengths, "analytic_check": analytic}, indent=2))
    print("Coordinate baselines are measured from the BS HR-face center.")
    print("The plate substrate can change actual geometric and optical path lengths.")
    if args.check_only:
        print("CHECK ONLY: no Fintrace model was built and no simulated results were produced.")
        return 0

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if args.legacy_lens_shim:
        import finesse.components as components
        if not hasattr(components, "AstigmaticLens"):
            # The validated topology contains no Lens objects. This only supplies
            # an import name needed by some older cosmicexplorer/Finesse pairs.
            components.AstigmaticLens = components.Lens
            print("WARNING: enabled the legacy import alias; this does not model astigmatic lenses.")
    try:
        from fintrace.model import FintraceModel
    except ImportError as exc:
        raise RuntimeError("Activate your working Fintrace/Finesse environment. If the error names AstigmaticLens, retry this lens-free model with --legacy-lens-shim.") from exc

    args.out.mkdir(parents=True, exist_ok=True)
    report = {"status": "building", "yaml": str(args.yaml.resolve()),
              "yaml_sha256": hashlib.sha256(args.yaml.read_bytes()).hexdigest(),
              "versions": versions(), "coordinate_lengths": lengths,
              "analytic_check": analytic, "simulated_paths": [],
              "scope": "Outgoing arm beam propagation only; no noise budget, return overlap or SNR."}
    def save_report():
        (args.out/"run_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    save_report()
    try:
        model = FintraceModel()
        model.lambda0 = float(cfg["Laser"]["Wavelength"])
        built = model.build_from_yaml(str(args.yaml.resolve()), gtrace=True, verbose=True)
        if not isinstance(built, (list, tuple)) or len(built) != 3:
            raise RuntimeError("Unexpected Fintrace build return. Expected (gdict, cavities, detectors).")
        gdict, cavities, detectors = built
        if not math.isclose(float(model.lambda0), float(cfg["Laser"]["Wavelength"]), rel_tol=1e-10):
            raise RuntimeError("Finesse wavelength differs from YAML; check your Fintrace version.")

        # Native Finesse solution.plot avoids Fintrace.plot_beam_trace API drift.
        # 'x'/'y' below name transverse planes, not the X/Y interferometer arms.
        for arm, target in (("X", "MX.fr.i"), ("Y", "MY.fr.i")):
            for plane in ("x", "y"):
                sol = model.propagate_beam(from_node="Laser.fr.o", to_node=target,
                                           q_in=q0, direction=plane)
                print(f"\n{arm} arm, transverse plane {plane}:\n{sol}")
                fig, _ = sol.plot("beamsize", "gouy", "curvature", show=False)
                fig.suptitle(f"iLILA {arm} arm: outgoing beam, transverse plane {plane}")
                fig.savefig(args.out/f"{arm.lower()}_arm_{plane}.png", dpi=180, bbox_inches="tight")
                plt.close(fig)
                row = {"arm": arm, "plane": plane,
                       "laser_to_end_geometric_m": float(sol.path_length),
                       "laser_to_end_optical_m": float(sol.optical_path_length)}
                report["simulated_paths"].append(row)
                print(json.dumps(row, indent=2))
        report["status"] = "beam_traces_complete"
        save_report()
        if not args.skip_layout:
            print("\nRendering the kilometer-scale layout. Central optics appear very small at this scale.")
            model.gtrace_plot(gdict, finesse_cavities=cavities, finesse_detectors=detectors,
                              render=True, beam_origin="laser", grid=True, draw_width=True,
                              savefile=str(args.out/"ilila_1km_layout"), img_res=1600,
                              power_threshold=1e-3)
        report["status"] = "complete"
        report["layout_rendered"] = not args.skip_layout
        save_report()
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = repr(exc)
        save_report()
        raise
    print(f"\nDone: {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
