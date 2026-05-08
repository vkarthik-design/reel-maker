import streamlit as st
import os
import glob

# Handling MoviePy version differences (v1.x vs v2.x)
try:
    from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
except ImportError:
    from moviepy import ImageClip, concatenate_videoclips, AudioFileClip

import yt_dlp

# --- 1. INITIALIZE STATE ---
if 'audio_path' not in st.session_state:
    st.session_state['audio_path'] = None

if 'yt_error' not in st.session_state:
    st.session_state['yt_error'] = None


# --- 2. DEFINE ALL FUNCTIONS ---

def cleanup_temp_files():
    """Removes temporary files and resets memory."""
    
    files = glob.glob("temp_*") + ["output_video.mp4"]

    for f in files:
        try:
            os.remove(f)
        except:
            pass

    st.session_state['audio_path'] = None
    st.session_state['yt_error'] = None


def download_youtube_audio(url):
    """Downloads audio from YouTube."""

    audio_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(audio_opts) as ydl:
        ydl.download([url])

    return "temp_audio.mp3"


def handle_youtube_download(url):
    """Handles YouTube audio download."""

    try:
        st.session_state['yt_error'] = None

        res_path = download_youtube_audio(url)

        if res_path:
            st.session_state['audio_path'] = res_path

    except Exception as e:
        st.session_state['yt_error'] = str(e)


def create_video(image_files, duplicate_count, fps, audio_path):
    """Creates video from images and audio."""

    clips = []

    duration_per_image = duplicate_count / fps
    target_resolution = (1280, 720)

    for idx, img_file in enumerate(image_files):

        temp_img_path = f"temp_img_{idx}.png"

        with open(temp_img_path, "wb") as f:
            f.write(img_file.getbuffer())

        clip = ImageClip(temp_img_path).with_duration(duration_per_image)
        clip = clip.resized(target_resolution)

        clips.append(clip)

    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.with_fps(fps)

    audio_clip = AudioFileClip(audio_path)

    if audio_clip.duration > final_video.duration:
        audio_clip = audio_clip.with_duration(final_video.duration)

    final_clip = final_video.with_audio(audio_clip)

    output_filename = "output_video.mp4"

    final_clip.write_videofile(
        output_filename,
        codec="libx264",
        audio_codec="aac"
    )

    return output_filename


# --- 3. STREAMLIT UI LOGIC ---

st.set_page_config(
    page_title="PragyanAI Video Creator",
    layout="wide"
)

# Display logo
if os.path.exists("BMW.jpg"):
    st.image("BMW.jpg")

st.title("PragyanAI - Multimedia Merger")

st.markdown(
    "Upload multiple images, specify timing, and add audio from a file or YouTube."
)

# Sidebar
with st.sidebar:

    st.header("Video Settings")

    fps = st.slider(
        "Frames Per Second (FPS)",
        1,
        60,
        24
    )

    duplicates = st.number_input(
        "Frames per Image",
        min_value=1,
        value=48
    )

    if st.button("Clear Cache & Temp Files"):
        cleanup_temp_files()
        st.rerun()

# Main Layout
col1, col2 = st.columns(2)

# Image Upload
with col1:

    st.subheader("1. Images")

    uploaded_images = st.file_uploader(
        "Upload Image Sequence",
        type=["jpg", "png", "jpeg"],
        accept_multiple_files=True
    )

# Audio Section
with col2:

    st.subheader("2. Audio")

    uploaded_audio = st.file_uploader(
        "Upload Audio File",
        type=["mp3", "wav"]
    )

    youtube_url = st.text_input("Or Paste YouTube URL")

    if st.button("Download YouTube Audio"):

        if youtube_url:
            handle_youtube_download(youtube_url)

    if st.session_state['yt_error']:
        st.error(st.session_state['yt_error'])

# Generate Video
st.subheader("3. Create Video")

if st.button("Generate Video"):

    if not uploaded_images:
        st.warning("Please upload images.")

    else:

        audio_path = None

        # Uploaded audio
        if uploaded_audio:

            audio_path = "temp_uploaded_audio.mp3"

            with open(audio_path, "wb") as f:
                f.write(uploaded_audio.read())

        # YouTube audio
        elif st.session_state['audio_path']:

            audio_path = st.session_state['audio_path']

        else:
            st.warning("Please upload audio or use YouTube URL.")

        if audio_path:

            with st.spinner("Creating video..."):

                output_video = create_video(
                    uploaded_images,
                    duplicates,
                    fps,
                    audio_path
                )

            st.success("Video Created Successfully!")

            st.video(output_video)

            with open(output_video, "rb") as file:

                st.download_button(
                    label="Download Video",
                    data=file,
                    file_name="output_video.mp4",
                    mime="video/mp4"
                )
