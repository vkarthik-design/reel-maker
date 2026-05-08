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
    """Downloads only audio from YouTube using reliable browser impersonation."""

    audio_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://www.google.com/',
        },
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
    """Callback function to ensure session state persists after button click."""

    try:
        st.session_state['yt_error'] = None

        res_path = download_youtube_audio(url)

        if res_path:
            st.session_state['audio_path'] = res_path

    except Exception as e:
        st.session_state['yt_error'] = str(e)


def create_video(image_files, duplicate_count, fps, audio_path):
    """Processes images and merges with audio using MoviePy."""

    clips = []

    duration_per_image = duplicate_count / fps
    target_resolution = (1280, 720)

    for idx, img_file in enumerate(image_files):

        temp_img_path = f"temp_img_{idx}.png"

        with open(temp_img_path, "wb") as f:
            f.write(img_file.getbuffer())

        # Compatible with MoviePy v1 and v2
        clip = ImageClip(temp_img_path)

        try:
            clip = clip.with_duration(duration_per_image)
            clip = clip.resized(target_resolution)
        except:
            clip = clip.set_duration(duration_per_image)
            clip = clip.resize(target_resolution)

        clips.append(clip)

    final_video = concatenate_videoclips(clips, method="compose")

    try:
        final_video = final_video.with_fps(fps)
    except:
        final_video = final_video.set_fps(fps)

    audio_clip = AudioFileClip(audio_path)

    if audio_clip.duration > final_video.duration:
        try:
            audio_clip = audio_clip.with_duration(final_video.duration)
        except:
            audio_clip = audio_clip.subclip(0, final_video.duration)

    try:
        final_clip = final_video.with_audio(audio_clip)
    except:
        final_clip = final_video.set_audio(audio_clip)

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

# Display logo if it exists
if os.path.exists("download.jpg"):
    st.image("download.jpg")

st.title("PragyanAI - Multimedia Merger")

st.markdown(
    "Upload multiple images, specify timing, and add audio from a file or YouTube."
)

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

col1, col2 = st.columns(2)

with col1:

    st.subheader("1. Images")

    uploaded_images = st.file_uploader(
        "Upload Image Sequence",
        type=["jpg", "png", "jpeg"],
        accept_multiple_files=True
    )

with col2:

    st.subheader("2. Audio")

    audio_option = st.radio(
        "Choose Audio Source",
        ["Upload Audio", "YouTube URL"]
    )

    if audio_option == "Upload Audio":

        uploaded_audio = st.file_uploader(
            "Upload Audio File",
            type=["mp3", "wav"]
        )

        if uploaded_audio:

            audio_path = f"temp_audio_{uploaded_audio.name}"

            with open(audio_path, "wb") as f:
                f.write(uploaded_audio.getbuffer())

            st.session_state['audio_path'] = audio_path

    else:

        yt_url = st.text_input("Enter YouTube URL")

        if st.button("Download YouTube Audio"):

            if yt_url:
                handle_youtube_download(yt_url)

        if st.session_state['yt_error']:
            st.error(st.session_state['yt_error'])

        if st.session_state['audio_path']:
            st.success("YouTube audio downloaded successfully!")

st.divider()

if st.button("Create Video"):

    if not uploaded_images:
        st.error("Please upload images.")

    elif not st.session_state['audio_path']:
        st.error("Please provide audio.")

    else:

        with st.spinner("Creating video..."):

            try:
                output_video = create_video(
                    uploaded_images,
                    duplicates,
                    fps,
                    st.session_state['audio_path']
                )

                st.success("Video created successfully!")

                st.video(output_video)

                with open(output_video, "rb") as file:
                    st.download_button(
                        label="Download Video",
                        data=file,
                        file_name="output_video.mp4",
                        mime="video/mp4"
                    )

            except Exception as e:
                st.error(f"Error creating video: {e}")
