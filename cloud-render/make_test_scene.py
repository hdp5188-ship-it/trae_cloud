"""Build a tiny test scene: a capsule-ish figure, camera push, pulsing red alarm light."""
import argparse
import os
import sys

import bpy


def args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--frames", type=int, default=120)
    return parser.parse_args(argv)


def material(name, color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def main() -> None:
    config = args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    collection = scene.collection

    scene.render.engine = "CYCLES"
    scene.frame_start = 1
    scene.frame_end = config.frames

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs[0].default_value = (0.015, 0.02, 0.035, 1.0)
    background.inputs[1].default_value = 0.35
    scene.world = world

    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "Ground"
    ground.data.materials.append(material("GroundMat", (0.09, 0.1, 0.12), 0.0, 0.7))

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.1))
    body = bpy.context.object
    body.name = "Body"
    body.scale = (0.55, 0.55, 1.1)
    body.data.materials.append(material("BodyMat", (0.45, 0.06, 0.05), 0.35, 0.35))

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.38, location=(0, 0, 2.55))
    head = bpy.context.object
    head.name = "Head"
    head.data.materials.append(material("HeadMat", (0.62, 0.5, 0.42), 0.05, 0.55))

    target = bpy.data.objects.new("Target", None)
    collection.objects.link(target)
    target.location = (0, 0, 1.45)

    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    collection.objects.link(camera)
    scene.camera = camera
    camera.location = (0, -7.5, 2.8)
    track = camera.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    camera.keyframe_insert("location", frame=1)
    camera.location = (0, -4.8, 2.5)
    camera.keyframe_insert("location", frame=config.frames)

    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 0.6
    sun_data.color = (0.55, 0.65, 1.0)
    sun = bpy.data.objects.new("Sun", sun_data)
    collection.objects.link(sun)
    sun.rotation_euler = (0.7, 0.2, 0.4)

    alarm_data = bpy.data.lights.new("Alarm", type="AREA")
    alarm_data.shape = "RECTANGLE"
    alarm_data.size = 4.0
    alarm_data.size_y = 2.0
    alarm_data.color = (1.0, 0.08, 0.04)
    alarm = bpy.data.objects.new("Alarm", alarm_data)
    collection.objects.link(alarm)
    alarm.location = (3.2, -2.4, 3.4)
    alarm_track = alarm.constraints.new(type="TRACK_TO")
    alarm_track.target = target
    alarm_track.track_axis = "TRACK_NEGATIVE_Z"
    alarm_track.up_axis = "UP_Y"

    total = config.frames
    for frame, energy in (
        (1, 30),
        (int(total * 0.25), 320),
        (int(total * 0.42), 60),
        (int(total * 0.62), 280),
        (int(total * 0.8), 90),
        (total, 240),
    ):
        alarm_data.energy = energy
        alarm_data.keyframe_insert("energy", frame=frame)

    out = os.path.abspath(config.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print(f"[scene] saved {out} ({total} frames)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"[scene] failed: {exc}", file=sys.stderr)
        raise
