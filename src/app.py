import os
import traceback

import pandas as pd
import streamlit as st

from predict_new import predict

# =====================================================
# Page Config
# =====================================================

st.set_page_config(
    page_title="उच्चारण | Nepali Pronunciation Evaluation",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# =====================================================
# Paths
# =====================================================

TEMP_FOLDER = "../temp"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# =====================================================
# Theme — custom CSS
# =====================================================
# Palette (Himalayan dusk, not a stock AI palette):
#   parchment  #FAF6EF   background
#   indigo     #1C2541   ink / headers
#   marigold   #E8A33D   accent / CTA
#   maroon     #8E2C3B   "needs work" state
#   pine       #2F6B4F   "good" state
#   slate      #5C6478   secondary text
#
# Type: Noto Serif Devanagari for the Nepali sentence itself
# (the one place the script needs real presence), Inter for
# the app chrome and data so the dashboard stays legible.

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+Devanagari:wght@500;700&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --parchment: #FAF6EF;
        --indigo: #1C2541;
        --marigold: #E8A33D;
        --maroon: #8E2C3B;
        --pine: #2F6B4F;
        --slate: #5C6478;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: var(--parchment);
    }

    /* ---- Hero ---- */
    .hero-title {
        font-family: 'Noto Serif Devanagari', serif;
        font-size: 2.1rem;
        font-weight: 700;
        color: var(--indigo);
        margin-bottom: 0.1rem;
    }
    .hero-sub {
        color: var(--slate);
        font-size: 0.98rem;
        margin-bottom: 1.4rem;
    }

    /* ---- Step rail ---- */
    .step-rail {
        display: flex;
        justify-content: space-between;
        margin: 0.5rem 0 1.6rem 0;
    }
    .step {
        flex: 1;
        text-align: center;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #E4DDCE;
        color: var(--slate);
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .step.active {
        border-bottom: 3px solid var(--marigold);
        color: var(--indigo);
    }
    .step-num {
        display: inline-block;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: var(--indigo);
        color: var(--parchment);
        font-size: 0.72rem;
        line-height: 20px;
        margin-right: 4px;
    }
    .step.active .step-num {
        background: var(--marigold);
        color: var(--indigo);
    }

    /* ---- Sentence card ---- */
    .sentence-card {
        background: #FFFFFF;
        border: 1px solid #E4DDCE;
        border-left: 6px solid var(--marigold);
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
    }
    .sentence-text {
        font-family: 'Noto Serif Devanagari', serif;
        font-size: 1.65rem;
        color: var(--indigo);
        line-height: 1.6;
    }

    /* ---- Section labels ---- */
    .section-label {
        font-weight: 600;
        color: var(--indigo);
        font-size: 0.95rem;
        margin: 1.2rem 0 0.4rem 0;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-size: 0.78rem;
        color: var(--slate);
    }

    /* ---- Result banner ---- */
    .result-banner {
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
        font-weight: 600;
        font-size: 1.05rem;
    }
    .result-good {
        background: #E7F1EA;
        color: var(--pine);
        border: 1px solid #B9DAC3;
    }
    .result-bad {
        background: #F5E6E9;
        color: var(--maroon);
        border: 1px solid #E3B9C1;
    }

    /* ---- Buttons ---- */
    div.stButton > button {
        background: var(--indigo);
        color: var(--parchment);
        border-radius: 8px;
        border: none;
        font-weight: 600;
        padding: 0.6rem 1rem;
    }
    div.stButton > button:hover {
        background: var(--marigold);
        color: var(--indigo);
    }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E4DDCE;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================
# Session State
# =====================================================

if "audio_path" not in st.session_state:
    st.session_state.audio_path = None
if "result" not in st.session_state:
    st.session_state.result = None

# =====================================================
# Sidebar — controls & instructions
# =====================================================

with st.sidebar:
    st.markdown("### Settings")

    gender = st.radio(
        "Reference voice",
        ["Male", "Female"],
        horizontal=True,
    )

    st.divider()

    st.markdown(
        """
        **How it works**
        1. Pick a sentence
        2. Listen to the reference
        3. Record yourself saying it
        4. Get an instant evaluation
        """
    )

# =====================================================
# Hero
# =====================================================

st.markdown('<div class="hero-title">🎙️ उच्चारण मूल्याङ्कन</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">AI-based Nepali Pronunciation Evaluation — read the sentence, record your voice, and see how close you are to the native reference.</div>',
    unsafe_allow_html=True,
)

# step indicator: which stage are we visually in
stage = 1
if st.session_state.audio_path:
    stage = 2
if st.session_state.result:
    stage = 3

steps = ["1 · Select sentence", "2 · Record", "3 · Result"]
rail_html = '<div class="step-rail">'
for i, label in enumerate(steps, start=1):
    cls = "step active" if i == stage else "step"
    rail_html += f'<div class="{cls}">{label}</div>'
rail_html += "</div>"
st.markdown(rail_html, unsafe_allow_html=True)

# =====================================================
# Reference Folder (Gender-Based) — load safely
# =====================================================

REFERENCE_FOLDER = f"../dataset/{gender.lower()}/app_reference/"
sentences_csv = os.path.join(REFERENCE_FOLDER, "sentences.csv")

if not os.path.isdir(REFERENCE_FOLDER):
    st.error(
        f"Reference folder not found:\n`{os.path.abspath(REFERENCE_FOLDER)}`\n\n"
        "Check that the `dataset/male` and `dataset/female` folders sit next to this app, "
        "or update `REFERENCE_FOLDER` in the code."
    )
    st.stop()

if not os.path.isfile(sentences_csv):
    st.error(f"`sentences.csv` not found inside `{REFERENCE_FOLDER}`.")
    st.stop()

try:
    df = pd.read_csv(sentences_csv)
except Exception as e:
    st.error(f"Could not read `sentences.csv`: {e}")
    st.stop()

required_cols = {"audio_id", "sentence"}
if not required_cols.issubset(df.columns):
    st.error(
        f"`sentences.csv` must contain columns {required_cols}, found {list(df.columns)}."
    )
    st.stop()

if df.empty:
    st.warning("No sentences available for this voice yet.")
    st.stop()

# =====================================================
# Sentence Selection
# =====================================================

st.markdown('<div class="section-label">Step 1 · Choose a sentence</div>', unsafe_allow_html=True)

voice = st.selectbox("Sentence", df["audio_id"], label_visibility="collapsed")
row = df[df["audio_id"] == voice].iloc[0]
sentence = row["sentence"]

st.markdown(
    f'<div class="sentence-card"><div class="sentence-text">{sentence}</div></div>',
    unsafe_allow_html=True,
)

reference_audio = os.path.join(REFERENCE_FOLDER, f"{voice}.wav")

if os.path.isfile(reference_audio):
    st.caption("Reference pronunciation")
    st.audio(reference_audio)
else:
    st.warning(f"Reference audio missing: `{reference_audio}`")

st.divider()

# =====================================================
# User Recording
# =====================================================

st.markdown('<div class="section-label">Step 2 · Record your voice</div>', unsafe_allow_html=True)

audio = st.audio_input("Click the microphone and record", label_visibility="collapsed")

if audio is not None:
    audio_path = os.path.join(TEMP_FOLDER, "user.wav")
    try:
        with open(audio_path, "wb") as f:
            f.write(audio.read())
        st.session_state.audio_path = audio_path
        st.session_state.result = None  # invalidate stale result on new recording
        st.success("Recording saved.")
        st.audio(audio_path)
    except Exception as e:
        st.error(f"Could not save your recording: {e}")

st.divider()

# =====================================================
# Evaluation
# =====================================================

st.markdown('<div class="section-label">Step 3 · Evaluate</div>', unsafe_allow_html=True)

evaluate_clicked = st.button("Evaluate Pronunciation", use_container_width=True)

if evaluate_clicked:
    if not st.session_state.audio_path or not os.path.isfile(st.session_state.audio_path):
        st.error("Please record your pronunciation first.")
    else:
        with st.spinner("Evaluating pronunciation..."):
            try:
                prediction, confidence, features = predict(
                    st.session_state.audio_path,
                    voice,
                    gender.lower(),
                )
                st.session_state.result = {
                    "prediction": prediction,
                    "confidence": confidence,
                    "features": features,
                }
            except Exception as e:
                st.session_state.result = None
                st.error(f"Evaluation failed: {e}")
                with st.expander("Technical error details"):
                    st.code(traceback.format_exc())

# =====================================================
# Result Display
# =====================================================

result = st.session_state.result

if result:
    prediction = result["prediction"]
    confidence = result["confidence"]
    features = result["features"]

    dtw = features.get("dtw", 0)
    duration = features.get("duration", 0)
    wer = features.get("wer", 0)
    cer = features.get("cer", 0)
    zcr = features.get("zcr", 0)

    if prediction == "Good":
        st.markdown(
            '<div class="result-banner result-good">✅ Good Pronunciation — close to the native reference.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="result-banner result-bad">❌ Needs Work — differs from the reference. Listen again and retry.</div>',
            unsafe_allow_html=True,
        )

    st.caption("Confidence")
    conf_val = max(0.0, min(100.0, float(confidence)))
    st.progress(conf_val / 100)
    st.markdown(f"**{conf_val:.1f}%**")

    with st.expander("Show technical details"):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("DTW Distance", f"{dtw:.4f}")
            st.metric("WER", f"{wer:.4f}")
        with col2:
            st.metric("Duration Difference", f"{duration:.2f} sec")
            st.metric("CER", f"{cer:.4f}")
        st.metric("ZCR", f"{zcr:.4f}")