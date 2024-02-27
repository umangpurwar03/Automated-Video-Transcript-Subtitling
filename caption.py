from moviepy.editor import VideoFileClip

def video_to_audio(input_video, output_audio):
    try:
        # Load the video clip
        video_clip = VideoFileClip(input_video)

        # Extract audio from the video
        audio_clip = video_clip.audio

        # Write the audio to a file
        audio_clip.write_audiofile(output_audio, codec='mp3')

        print(f"Audio extracted successfully: {output_audio}")

    except Exception as e:
        print(f"Error: {e}")

# Example usage
video_input_file = r"instagram_vedio_caption_generator\test.mp4"
audio_output_file = r"instagram_vedio_caption_generator\audio.mp3"

video_to_audio(video_input_file, audio_output_file)
