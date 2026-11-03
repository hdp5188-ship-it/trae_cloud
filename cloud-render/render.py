"""Run inside Blender: blender -b scene.blend -P render.py -- --out ..."""
import argparse
import os
import sys

import bpy


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--device", default="auto", choices=["auto", "gpu", "cpu"])
    return parser.parse_args(argv)


def setup_device(scene, mode: str) -> None:
    scene.render.engine = "CYCLES"
    scene.cycles.use_adaptive_sampling = True
    if mode == "cpu":
        scene.cycles.device = "CPU"
        return
    prefs = bpy.context.preferences.addons.get("cycles")
    if not prefs:
        scene.cycles.device = "CPU"
        return
    try:
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        devices = list(prefs.devices)
        gpus = [device for device in devices if device.type != "CPU"]
        if gpus:
            for device in devices:
                device.use = device.type != "CPU"
            scene.cycles.device = "GPU"
            print(f"[render] GPU devices: {[device.name for device in gpus]}")
        else:
            scene.cycles.device = "CPU"
            print("[render] no CUDA device found, falling back to CPU")
    except Exception as exc:  # noqa: BLE001 - never fail the render on device setup
        scene.cycles.device = "CPU"
        print(f"[render] GPU setup failed ({exc}), falling back to CPU")


def main() -> None:
    args = parse_args()
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    scene = bpy.context.scene
    setup_device(scene, args.device)

    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True

    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0

    scene.render.fps = args.fps
    scene.render.fps_base = 1.0
    scene.frame_start = args.start
    scene.frame_end = args.end
    scene.frame_step = 1

    scene.render.use_file_extension = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 15
    scene.render.filepath = os.path.join(out_dir, "frame_")
    scene.render.use_overwrite = True
    scene.render.use_placeholder = False

    print(
        f"[render] {args.width}x{args.height} @ {args.fps}fps, "
        f"frames {args.start}-{args.end}, samples {args.samples}, "
        f"device {scene.cycles.device}"
    )
    bpy.ops.render.render(animation=True)
    print("[render] finished")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - surface a non-zero exit for the worker
        print(f"[render] failed: {exc}", file=sys.stderr)
        raise
