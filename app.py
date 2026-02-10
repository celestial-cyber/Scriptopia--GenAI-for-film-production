import json
import os
from video_engine.extract_frames import extract_frames
from core.intent_engine import interpret_intent
from video_engine.frame_graph_api import build_frame_graph, traverse_frame_graph
from video_engine.regenerate_api import regenerate_video

DATA_INPUT = os.path.join("data", "input_videos")
DATA_FRAMES = os.path.join("data", "frames")
DATA_OUTPUTS = os.path.join("data", "outputs")
DATA_STATES = os.path.join("data", "states")

os.makedirs(DATA_STATES, exist_ok=True)

VIDEO_PATH = os.path.join(DATA_INPUT, "326677_small.mp4")
FRAME_DIR = DATA_FRAMES
OUTPUT_VIDEO = os.path.join(DATA_OUTPUTS, "output.mp4")

# Step 1: Extract frames
extract_frames(VIDEO_PATH, FRAME_DIR)

# Step 2: User input
user_input = input("Describe the style you want (cinematic / fast / reel): ")
fps_input = input("Optional FPS (press Enter to use default): ").strip()
fps = int(fps_input) if fps_input else None

# Step 3: Intent Understanding
intent = interpret_intent(user_input)
if fps is not None:
    intent["fps"] = fps

# Step 4: Frame Graph Traversal
frames = build_frame_graph(FRAME_DIR)
frame_path = traverse_frame_graph(frames, intent)

# Step 5: Regenerate Video
regenerate_video(
    FRAME_DIR,
    frame_path,
    OUTPUT_VIDEO,
    intent
)

# Step 6: Save Creative State
state = {
    "intent": intent,
    "frame_path_length": len(frame_path),
    "output_video": OUTPUT_VIDEO
}

with open(os.path.join(DATA_STATES, "state_1.json"), "w") as f:
    json.dump(state, f, indent=2)

print("[DONE] Creative state saved")
