from moviepy.editor import ImageSequenceClip
from PIL import Image
import os


def regenerate_video(frame_dir, frame_path, output_path, intent):
    """Assemble a video from frames locally using `intent` for parameters.

    `intent` is expected to be a dict produced by `core.intent_engine.interpret_intent`.
    """
    images = [os.path.join(frame_dir, f) for f in frame_path]

    # Filter out corrupted frames
    valid_images = []
    for img_path in images:
        try:
            with Image.open(img_path) as img:
                img.verify()
            valid_images.append(img_path)
        except Exception as e:
            print(f"[WARN] Skipping corrupted frame: {img_path} ({str(e)})")

    if not valid_images:
        print("[ERROR] No valid frames found!")
        return

    print(f"[INFO] Using {len(valid_images)} valid frames (skipped {len(images) - len(valid_images)})")

    fps = None
    if isinstance(intent, dict):
        fps = intent.get("fps")
    if not fps:
        fps = 24

    clip = ImageSequenceClip(valid_images, fps=fps)
    clip.write_videofile(output_path, codec="libx264", verbose=False, logger=None)

    print(f"[INFO] Video regenerated at {output_path}")
