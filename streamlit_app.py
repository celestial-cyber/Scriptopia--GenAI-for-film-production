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


st.set_page_config(page_title="Scriptoria - Theatrical Video Remix", layout="wide")

# Theatrical / Cinematic Theme
st.markdown(
    """
<style>
:root {
  --text: #f1f5f9;
  --panel: rgba(20, 10, 30, 0.75); /* Deep purple/black glass */
  --panel-border: rgba(212, 175, 55, 0.3); /* Gold border */
  --primary: #d4af37; /* Gold */
  --primary-hover: #fcd34d;
  --secondary: #be123c; /* Deep red (theater curtains) */
  --shadow: rgba(0, 0, 0, 0.5);
}

/* Dynamic Theatrical Gradient Background */
[data-testid="stAppViewContainer"] {
  background-color: #0f0518;
  background-image:
    radial-gradient(at 10% 10%, rgba(190, 18, 60, 0.25) 0px, transparent 60%), /* Red Spotlight */
    radial-gradient(at 90% 10%, rgba(212, 175, 55, 0.15) 0px, transparent 60%), /* Gold Light */
    radial-gradient(at 50% 90%, rgba(88, 28, 135, 0.3) 0px, transparent 60%); /* Purple Depth */
  background-attachment: fixed;
}

[data-testid="stAppViewContainer"]::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  backdrop-filter: blur(50px);
  z-index: -1;
}

.main .block-container {
  max-width: 1200px;
  padding-top: 2rem;
  padding-bottom: 4rem;
}

/* Cinematic Glass Panels */
.glass {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 10px 40px var(--shadow);
  margin-bottom: 1.5rem;
}

/* Typography */
h1, h2, h3 {
  color: #fbbf24 !important; /* Gold text for headers */
  font-family: 'Cinzel', 'Playfair Display', serif; /* Serif for theatrical feel */
  letter-spacing: 0.05em;
  font-weight: 700;
  text-shadow: 0 2px 10px rgba(0,0,0,0.5);
}

p, label, li, .stMarkdown, .stText {
  color: #e2e8f0 !important;
  font-family: 'Inter', sans-serif;
}

/* Buttons */
.stButton > button {
  border: 1px solid #d4af37;
  border-radius: 4px;
  padding: 0.6rem 1.5rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #0f0518;
  background: linear-gradient(135deg, #d4af37 0%, #fcd34d 100%);
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
}

.stButton > button:hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(212, 175, 55, 0.5);
  color: #0f0518;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
  background-color: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(212, 175, 55, 0.3);
  color: #e2e8f0;
  border-radius: 6px;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.2);
}

/* File Uploader */
div[data-testid="stFileUploader"] section {
  background-color: rgba(0, 0, 0, 0.4);
  border: 1px dashed rgba(212, 175, 55, 0.4);
  border-radius: 8px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
  background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
  height: 45px;
  border-radius: 4px;
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid transparent;
  color: #94a3b8;
  font-family: 'Cinzel', serif;
}

.stTabs [aria-selected="true"] {
  background-color: rgba(212, 175, 55, 0.1) !important;
  border-color: var(--primary) !important;
  color: #d4af37 !important;
  font-weight: 600;
}

/* Expander */
div[data-testid="stExpander"] {
  background-color: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}
</style>
""",
    unsafe_allow_html=True,
)

# --- Sidebar for Keys ---
with st.sidebar:
    st.title("⚙️ Settings")
    api_key_input = st.text_input("Groq API Key", type="password", help="Enter your Groq API Key here if not set in environment.")
    if api_key_input:
        os.environ["GROQ_API_KEY"] = api_key_input

st.title("🎬 Scriptoria")
st.caption("The AI-Powered Cinematic Video Remix Studio")

# --- Layout: Main Control Panel ---
st.markdown('<div class="glass">', unsafe_allow_html=True)
col1, col2 = st.columns([1.8, 1])

with col1:
    st.subheader("🎥 Input Footage")
    uploaded = st.file_uploader("Upload video (MP4, MOV, AVI)", type=["mp4", "mov", "avi"])
    style_text = st.text_input(
        "Directorial Vision (Style Prompt)",
        value="cinematic dramatic 15fps",
        help="Describe the desired output style (e.g., 'noir mystery 24fps slow motion')",
    )

with col2:
    st.subheader("🛠️ Production Controls")
    use_llm = st.toggle("Use AI for Intent", value=True)
    use_llm_preprod = st.toggle("Use AI for Planning", value=True)
    fps_input = st.number_input("Target FPS (0 = Auto)", min_value=0, max_value=60, value=0)

st.markdown("</div>", unsafe_allow_html=True)

# --- Action Section ---
if uploaded:
    st.success(f"Reel Loaded: {uploaded.name} ({uploaded.size / 1e6:.1f} MB)")

if st.button("🚀 Action! (Generate Video & Plan)", use_container_width=True):
    if not uploaded:
        st.error("Please upload a video file first.")
    else:
        # Check API Key
        if (use_llm or use_llm_preprod) and not os.environ.get("GROQ_API_KEY"):
            st.warning("⚠️ No Groq API Key detected. AI features may fail. Please enter it in the sidebar.")

        # Processing Logic
        with st.status("Production in progress...", expanded=True) as status:
            st.write("📥 Ingesting daily rushes (saving upload)...")
            input_path = os.path.join(DATA_INPUT, uploaded.name)
            with open(input_path, "wb") as f:
                shutil.copyfileobj(uploaded, f)

            st.write("🎞️ Cutting negative (extracting frames)...")
            try:
                shutil.rmtree(DATA_FRAMES)
            except Exception:
                pass
            os.makedirs(DATA_FRAMES, exist_ok=True)
            extract_frames(input_path, DATA_FRAMES)

            st.write("🧠 Director's interpretation (analyzing intent)...")
            intent = interpret_intent(style_text, use_llm=use_llm)
            if fps_input > 0:
                intent["fps"] = int(fps_input)

            st.write("📝 Writers' room (generating preproduction plan)...")
            preprod_result = run_preproduction(style_text, intent, use_llm=use_llm_preprod)

            status.update(label="Principal photography complete! Assembling final cut...", state="running")
            
            # Show Preprod Results in Tabs
            st.divider()
            t1, t2, t3, t4, t5 = st.tabs(["📜 Screenplay", "📋 Schedule", "🎭 Cast", "🎼 Score", "🍿 Final Cut"])

            with t1:
                st.subheader(preprod_result['screenplay'].get('title', 'Untitled Screenplay'))
                for scene in preprod_result["screenplay"].get("scenes", []):
                    st.markdown(f"**Scene {scene.get('id', '?')}**: {scene.get('description', '')} _({scene.get('rough_duration_s', 0)}s)_")

            with t2:
                wf = preprod_result.get("workflow", {})
                st.write(f"**Style:** {wf.get('style', 'N/A')} | **Pace:** {wf.get('pace', 'N/A')}")
                for step in wf.get("steps", []):
                    st.markdown(f"- **Phase {step.get('phase', '?')}**: {step.get('name', '')} _({step.get('notes', '')})_")

            with t3:
                chars = preprod_result.get("characters", {})
                st.write(f"**Mood:** {chars.get('primary_mood', 'N/A')}")
                for ch in chars.get("characters", []):
                    st.markdown(f"- **{ch.get('role', 'Unknown')}**: {ch.get('mood', '')} (Lighting: {ch.get('lighting', '')})")

            with t4:
                sound = preprod_result.get("sound_design", {})
                st.write(f"**Audio Style:** {sound.get('style', 'N/A')}")
                for track in sound.get("tracks", []):
                    st.markdown(f"- 🎵 {track.get('name', '')} ({track.get('type', '')})")

            with t5:
                st.info("Rendering final cut...")
                frames = build_frame_graph(DATA_FRAMES)
                frame_path = traverse_frame_graph(frames, intent)

                if not frame_path:
                    st.error("Could not select frames for this style.")
                else:
                    output_path = os.path.join(DATA_OUTPUTS, "output_remix.mp4")
                    regenerate_video(DATA_FRAMES, frame_path, output_path, intent)
                    st.video(output_path)
                    st.success(f"Cut! It's a wrap. ({len(frame_path)} frames)")

            status.update(label="Output ready for premiere!", state="complete")


# --- "Ask Scriptopia" Section ---
st.markdown('<div class="glass">', unsafe_allow_html=True)
st.subheader("✨ Ask Scriptopia")
st.caption("Consult the AI Director for creative vision and script ideas.")

groq_col1, groq_col2 = st.columns([3, 1])
with groq_col1:
    user_prompt = st.text_area(
        "Your Query",
        placeholder="E.g., 'Write a dramatic monologue for a villain in the rain.'",
        label_visibility="collapsed",
        height=100
    )

with groq_col2:
    st.write("") # Spacer
    st.write("") # Spacer
    consult_clicked = st.button("Consult AI", use_container_width=True)

if consult_clicked:
    if not user_prompt.strip():
        st.warning("Please enter a query.")
    else:
        if not os.environ.get("GROQ_API_KEY"):
            st.error("🚫 Missing Groq API Key.")
        else:
            with st.spinner("Consulting the archives..."):
                answer = request_text_from_llm(user_prompt.strip())
            
            if answer:
                st.markdown("### 🎭 Scriptopia's Vision")
                st.success(answer)
            else:
                st.error("No response from the oracle.")

st.markdown("</div>", unsafe_allow_html=True)