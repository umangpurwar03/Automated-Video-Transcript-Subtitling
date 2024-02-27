from pytube import YouTube

def download_youtube_video(video_url, output_path='.'):
    try:
        # Create a YouTube object
        yt = YouTube(video_url)

        # Get the highest resolution stream
        video_stream = yt.streams.get_highest_resolution()

        # Download the video to the specified output path
        video_stream.download(output_path)

        print(f"Downloaded: {yt.title}")
    except Exception as e:
        print(f"Error: {str(e)}")

# Example usage
video_url = 'https://youtu.be/4X_e3UWS9aA?si=BSpjvixkv-CQutnk'
output_path = 'instagram_vedio_caption_generator'
download_youtube_video(video_url, output_path)
