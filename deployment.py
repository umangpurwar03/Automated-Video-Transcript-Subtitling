import streamlit as st
from moviepy.editor import VideoFileClip, AudioFileClip
import torch
from transformers import pipeline
import cv2
import tempfile
import os
import shutil

# Function to add multiline text within the specified width
# Function to add multiline text within the specified width
def add_multiline_text(img, text, pos, font, font_size, font_color, max_width):
    words = text.split()
    lines = []
    current_line = words[0]

    for word in words[1:]:
        # Check the width of the current line with the new word
        (width, _), _ = cv2.getTextSize(current_line + " " + word, font, font_size, 2)

        if width <= max_width:
            # If the line fits within the width, add the word to the current line
            current_line += " " + word
        else:
            # If the line exceeds the width, start a new line
            lines.append(current_line)
            current_line = word

    # Add the last line
    lines.append(current_line)

    # Add each line to the image
    for i, line in enumerate(lines):
        y = pos[1] + i * int(1.5 * font_size)
        cv2.putText(img, line, (pos[0], y), font, font_size, font_color, 2)
# Function to convert Streamlit color string to tuple of integers
def st_color_to_tuple(color_str):
    # Check if the color string is in hexadecimal format
    if color_str.startswith("#") and (len(color_str) == 7 or len(color_str) == 9):
        # Extract RGB or RGBA values from the hexadecimal string
        rgb_values = [int(color_str[i:i + 2], 16) for i in (1, 3, 5)]
        return tuple(rgb_values)
    else:
        raise ValueError("Invalid color format. Please use a valid hexadecimal color string.")

# Function to get caption based on timestamp
def get_caption(timestamp, speech_chunks):
    for chunk in speech_chunks:
        start, end = chunk['timestamp']
        if start <= timestamp < end:
            return chunk['text']
    return ''  # No caption found for the given timestamp

# Use st.sidebar to place elements in the left sidebar
st.sidebar.title("Video Caption Generator")

# Streamlit color picker
font_color_str = st.sidebar.color_picker("Choose font color", "#ffffff")  # Default color is white
font_color = st_color_to_tuple(font_color_str)

# Additional components for font, font size, bold, and italic selection
font_options = ["cv2.FONT_HERSHEY_SIMPLEX", "cv2.FONT_HERSHEY_COMPLEX", "cv2.FONT_HERSHEY_SCRIPT_SIMPLEX",
                "cv2.FONT_HERSHEY_PLAIN", "cv2.FONT_HERSHEY_DUPLEX", "cv2.FONT_HERSHEY_TRIPLEX",
                "cv2.FONT_HERSHEY_COMPLEX_SMALL", "cv2.FONT_HERSHEY_SCRIPT_COMPLEX"]
font_name = st.sidebar.selectbox("Select font", font_options)
font_size = st.sidebar.slider("Select font size", min_value=1, max_value=10, value=1)
bold_text = st.sidebar.checkbox("Bold Text", False)
italic_text = st.sidebar.checkbox("Italic Text", False)

uploaded_file = st.sidebar.file_uploader("Upload a video file", type=["mp4"])

if uploaded_file:
    # Save the uploaded file to a temporary location
    video_input_path = os.path.join(tempfile.mkdtemp(), "uploaded_video.mp4")
    with open(video_input_path, "wb") as f:
        f.write(uploaded_file.read())

    st.sidebar.video(uploaded_file)

    if st.sidebar.button("Generate Caption"):
        # Function to extract audio from video
        def extract_audio_from_video(input_video_path, output_audio_path):
            try:
                # Load the video clip
                video_clip = VideoFileClip(input_video_path)

                # Extract audio from the video
                audio_clip = video_clip.audio

                # Write the audio to a temporary file
                temp_audio_path = os.path.join(tempfile.mkdtemp(), "temp_audio.mp3")
                audio_clip.write_audiofile(temp_audio_path, codec='mp3')

                # st.info(f"Audio extracted successfully: {temp_audio_path}")

                return temp_audio_path

            except Exception as e:
                # st.error(f"Error: {e}")
                return None

        # Extract audio from the uploaded video
        audio_temp_path = extract_audio_from_video(video_input_path, None)

        # Set up automatic speech recognition pipeline
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        asr_pipeline = pipeline(
            "automatic-speech-recognition",
            model='openai/whisper-large-v3',
            chunk_length_s=30,
            device=device,
        )

        # Perform speech recognition on the audio
        speech_prediction = asr_pipeline(audio_temp_path, batch_size=8, return_timestamps=True)

        # Define output video path
        output_video_path = os.path.join(tempfile.mkdtemp(), "temp_output.mp4")

        cap = cv2.VideoCapture(video_input_path)

        if not cap.isOpened():
            st.error("Error opening video file")

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Define the codec and create VideoWriter object
        video_codec = cv2.VideoWriter_fourcc(*'mp4v')  # You can change the codec as needed
        video_writer = cv2.VideoWriter(output_video_path, video_codec, fps, (width, height))

        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                # st.info("End of video")
                break

            current_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            caption = get_caption(current_timestamp, speech_prediction['chunks'])

            # Adjust font style based on the user's choice
            font_face = eval(font_name) | cv2.FONT_ITALIC if italic_text else eval(font_name)

            # Adjust thickness based on the user's choice
            thickness = 2 if not bold_text else 5

            # Add caption to frame with user-selected font, size, bold, and italic options
            cv2.putText(frame, caption, (50, 50), fontFace=font_face, fontScale=font_size,
                        color=font_color, thickness=thickness)

            # Add caption to frame
            # cv2.putText(frame, caption, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, font_color, 2)

            # Save the processed frame to the output video file
            video_writer.write(frame)

        # Release video capture and writer objects
        cap.release()
        video_writer.release()
        cv2.destroyAllWindows()

        # Merge audio and video files
        def merge_audio_video(audio_path, video_path, output_path):
            # Load the video clip
            video_clip = VideoFileClip(video_path)

            # Load the audio clip
            audio_clip = AudioFileClip(audio_path)

            # Set the audio of the video clip to the loaded audio clip
            video_clip = video_clip.set_audio(audio_clip)

            # Write the result to a temporary file
            temp_output_path = os.path.join(tempfile.mkdtemp(), "temp_merged_output.mp4")
            video_clip.write_videofile(temp_output_path, codec="libx264", audio_codec="aac")

            return temp_output_path

        # Example usage
        final_output_path = os.path.join(tempfile.mkdtemp(), "output1.mp4")
        merged_video_temp_path = merge_audio_video(audio_temp_path, output_video_path, final_output_path)

        # Display final output
        st.video(merged_video_temp_path)

        # Provide a download link for the final output
        st.sidebar.markdown(f"**Download Captioned Video**")
        st.sidebar.markdown(f"Click [here]({merged_video_temp_path}) to download the captioned video.")

        # Clean up temporary files
        os.remove(audio_temp_path)
        os.remove(output_video_path)
else:
    st.sidebar.warning("Please upload a video file.")
