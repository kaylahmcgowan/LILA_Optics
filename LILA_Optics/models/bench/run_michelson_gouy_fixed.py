"""Build, render, and Gaussian-beam trace the simple FinTrace Michelson."""

from pathlib import Path

# Compatibility shim for the older Finesse build supplied by the IGWN
# environment.  cosmicexplorer re-exports AstigmaticLens while this Michelson
# uses only the ordinary Lens class.  Supplying the missing export lets
# cosmicexplorer load without changing the optical model.
import finesse.components as finesse_components

if not hasattr(finesse_components, "AstigmaticLens"):
    finesse_components.AstigmaticLens = finesse_components.Lens

from fintrace.model import FintraceModel


HERE = Path(__file__).resolve().parent
YAML_FILE = HERE / "simple_michelson.yaml"
OUTPUT_DIR = HERE / "michelson_outputs"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    model = FintraceModel()
    print(f"Loading: {YAML_FILE}")
    gdict, cavities, detectors = model.build_from_yaml(
        str(YAML_FILE),
        gtrace=True,
        verbose=True,
    )

    print("\nRendering the interferometer and Gaussian-beam width...")
    model.gtrace_plot(
        gdict,
        finesse_cavities=cavities,
        finesse_detectors=detectors,
        render=True,
        beam_origin="laser",
        grid=True,
        draw_width=True,
        savefile=str(OUTPUT_DIR / "michelson_layout"),
        img_res=1000,
        power_threshold=1e-4,
    )

    print("\nTracing the transmitted X arm...")
    model.trace_beam(
        ["Laser.fr.o", "MX.fr.i"],
        q_at=[
            "L1.fr.i",
            "L1.bk.o",
            "BS.fr1.i",
            "BS.bk1.o",
            "MX.fr.i",
        ],
        plot=["beamsize", "gouy", "curvature"],
        savepath=str(OUTPUT_DIR / "x_arm"),
        direction="both",
        astig_difference=True,
    )

    print("\nTracing the reflected Y arm...")
    model.trace_beam(
        ["Laser.fr.o", "MY.fr.i"],
        q_at=[
            "L1.fr.i",
            "L1.bk.o",
            "BS.fr1.i",
            "BS.fr2.o",
            "MY.fr.i",
        ],
        plot=["beamsize", "gouy", "curvature"],
        savepath=str(OUTPUT_DIR / "y_arm"),
        direction="both",
        astig_difference=True,
    )

    print("\nDone. Outputs are in:")
    print(OUTPUT_DIR)


if __name__ == "__main__":
    main()
