import json
import os
import shutil

import streamlit as st

from core.intent_engine import interpret_intent
from core.llm_client import request_text_from_llm
from preproduction_engine.preprod_controller import run_preproduction
from video_engine.extract_frames import extract_frames
from video_engine.frame_graph_api import build_frame_graph, traverse_frame_graph
from video_engine.regenerate_api import regenerate_video


DATA_INPUT = os.path.join("data", "input_videos")
DATA_FRAMES = os.path.join("data", "frames")
DATA_OUTPUTS = os.path.join("data", "outputs")
DATA_STATES = os.path.join("data", "states")

os.makedirs(DATA_INPUT, exist_ok=True)
os.makedirs(DATA_FRAMES, exist_ok=True)
os.makedirs(DATA_OUTPUTS, exist_ok=True)
os.makedirs(DATA_STATES, exist_ok=True)


st.set_page_config(page_title="Scriptoria - Video Remix", layout="wide")

st.markdown(
    """
<style>
:root {
  --text: #0b1220;
  --panel: rgba(255, 255, 255, 0.62);
  --panel-border: rgba(255, 255, 255, 0.55);
  --primary: #0f766e;
  --primary-2: #2563eb;
  --shadow: rgba(15, 23, 42, 0.15);
}

[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1100px 700px at 8% 8%, rgba(15, 118, 110, 0.24), transparent 65%),
    radial-gradient(950px 580px at 90% 12%, rgba(37, 99, 235, 0.22), transparent 62%),
    radial-gradient(800px 540px at 50% 92%, rgba(14, 116, 144, 0.18), transparent 65%),
    linear-gradient(130deg, #dff4ff 0%, #edf9ff 38%, #f8fafc 100%);
}

[data-testid="stAppViewContainer"]::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  backdrop-filter: blur(2px);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.1));
}

.main .block-container {
  max-width: 1200px;
  padding-top: 2rem;
  padding-bottom: 2rem;
}

.glass {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: 18px;
  padding: 1rem 1.2rem;
  backdrop-filter: blur(18px) saturate(135%);
  box-shadow: 0 18px 45px var(--shadow);
}

h1, h2, h3 {
  color: var(--text);
  letter-spacing: -0.02em;
}

p, label, li, div {
  color: #0f172a;
}

.stButton > button {
  border: 0;
  border-radius: 12px;
  padding: 0.65rem 1.1rem;
  font-weight: 600;
  color: #ffffff;
  background: linear-gradient(90deg, var(--primary), var(--primary-2));
}

.stButton > button:hover {
  filter: brightness(1.05);
}

div[data-testid="stFileUploader"] section {
  border-radius: 14px;
  border: 1px dashed rgba(15, 23, 42, 0.22);
}

div[data-testid="stExpander"] {
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  overflow: hidden;
}
</style>
""",
    unsafe_allow_html=True,
)

st.title("Scriptoria - Interactive Video Remix")
st.caption("Generate remixed videos and preproduction plans from natural language prompts.")

st.markdown('<div class="glass">', unsafe_allow_html=True)
left, right = st.columns([2, 1])

with left:
    uploaded = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])
    style_text = st.text_input(
        "Describe the style",
        value="cinematic dramatic 15fps",
        help="Example: trailer energetic 20s with smooth dissolve and voiceover",
    )

with right:
    st.subheader("Options")
    use_llm = st.toggle("Use Groq for intent parsing", value=True)
    use_llm_preprod = st.toggle("Use Groq for preproduction writing", value=True)
    fps_input = st.number_input("FPS override (0 = auto)", min_value=0, max_value=60, value=0)
st.markdown("</div>", unsafe_allow_html=True)

if uploaded:
    st.info(f"Selected: {uploaded.name} ({uploaded.size / 1e6:.2f} MB)")

if st.button("Generate Video and Preproduction", use_container_width=True):
    if not uploaded:
        st.error("Upload a video first.")
    else:
        with st.spinner("Saving upload and extracting frames..."):
            input_path = os.path.join(DATA_INPUT, uploaded.name)
            with open(input_path, "wb") as f:
                shutil.copyfileobj(uploaded, f)

            try:
                shutil.rmtree(DATA_FRAMES)
            except Exception:
                pass
            os.makedirs(DATA_FRAMES, exist_ok=True)
            extract_frames(input_path, DATA_FRAMES)

        intent = interpret_intent(style_text, use_llm=use_llm)
        if fps_input > 0:
            intent["fps"] = int(fps_input)

        with st.expander("Interpreted Intent", expanded=False):
            st.json(intent)

        st.info("Running preproduction planning...")
        preprod_result = run_preproduction(style_text, intent, use_llm=use_llm_preprod)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Screenplay", "Workflow", "Characters", "Sound Design", "Video"]
        )

        with tab1:
            st.subheader("Screenplay")
            st.write(f"Title: {preprod_result['screenplay']['title']}")
            for scene in preprod_result["screenplay"]["scenes"]:
                st.write(
                    f"Scene {scene['id']}: {scene['description']} (~{scene['rough_duration_s']}s)"
                )

        with tab2:
            st.subheader("Production Workflow")
            wf = preprod_result["workflow"]
            st.write(f"Style: {wf['style']} | Pace: {wf['pace']}")
            for step in wf["steps"]:
                st.write(
                    f"Phase {step['phase']}: {step['name']} ({step['priority']}) - {step['notes']}"
                )

        with tab3:
            st.subheader("Characters and Subjects")
            chars = preprod_result["characters"]
            st.write(f"Primary mood: {chars['primary_mood']} | Count: {chars['count']}")
            for ch in chars["characters"]:
                st.write(
                    f"{ch['role']} ({ch['screen_time_pct']}% screen time) | Lighting: {ch['lighting']}"
                )

        with tab4:
            st.subheader("Sound Design Plan")
            sound = preprod_result["sound_design"]
            st.write(
                f"Style: {sound['style']} | Tracks: {sound['track_count']} | "
                f"Narration: {'Yes' if sound['has_narration'] else 'No'}"
            )
            for track in sound["tracks"]:
                st.write(
                    f"{track['name']} | Type: {track['type']} | Volume: {track['volume_db']}dB"
                )

        with tab5:
            st.info("Building frame graph and selecting frames...")
            frames = build_frame_graph(DATA_FRAMES)
            frame_path = traverse_frame_graph(frames, intent)

            if not frame_path:
                st.error("No frames were selected.")
            else:
                st.success(f"Selected {len(frame_path)} frames from {len(frames)} total.")
                output_path = os.path.join(DATA_OUTPUTS, "output_streamlit.mp4")
                with st.spinner("Assembling video..."):
                    regenerate_video(DATA_FRAMES, frame_path, output_path, intent)
                st.success("Video generated.")
                st.video(output_path)

                state = {
                    "intent": intent,
                    "frame_path_length": len(frame_path),
                    "output_video": output_path,
                    "preprod": preprod_result,
                }
                with open(os.path.join(DATA_STATES, "state_streamlit.json"), "w") as sf:
                    json.dump(state, sf, indent=2, default=str)
                st.caption("State saved to data/states/state_streamlit.json")

st.markdown('<div class="glass">', unsafe_allow_html=True)
st.subheader("Ask Groq (Text Output)")
user_prompt = st.text_area(
    "Ask for script ideas, scene notes, dialogue, or production guidance",
    placeholder="Write a moody 20-second opening narration for a city night scene...",
)
if st.button("Get Text from Groq"):
    if not user_prompt.strip():
        st.warning("Enter a prompt first.")
    else:
        with st.spinner("Querying Groq..."):
            answer = request_text_from_llm(user_prompt.strip())
        if answer:
            st.success("Response received.")
            st.write(answer)
        else:
            st.error(
                "No response from Groq. Verify GROQ_API_KEY and optional GROQ_MODEL in your environment."
            )
st.markdown("</div>", unsafe_allow_html=True)

st.caption(
    "Tip: set GROQ_API_KEY in your environment, then enable Groq intent parsing for richer prompt understanding."
)
