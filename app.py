from flask import Flask, request, jsonify, send_from_directory
from googleapiclient.discovery import build
import os
import yt_dlp
from waitress import serve
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

youtube_api_key = "YOUR_YOUTUBE_API_KEY"

# Replace with your Render domain
RENDER_DOMAIN = "https://your-render-app.onrender.com"

def get_video_id(song_name):
    """Fetch the video ID of a YouTube Music song using YouTube API."""
    try:
        youtube = build("youtube", "v3", developerKey=youtube_api_key)
        request = youtube.search().list(q=song_name, part="id", maxResults=1, type="video")
        response = request.execute()
        if "items" in response and len(response["items"]) > 0:
            return response["items"][0]["id"]["videoId"]
    except Exception as e:
        logging.error(f"Error fetching video ID: {str(e)}")
    return None

def download_audio(video_id):
    """Download audio from YouTube and save it as an MP3 file."""
    try:
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': f'static/{video_id}.mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
        
        return f'static/{video_id}.mp3'
    except Exception as e:
        logging.error(f"Error downloading audio: {str(e)}")
        return None

@app.route('/play', methods=['GET'])
def play_song():
    try:
        song_name = request.args.get('song')
        if not song_name:
            return jsonify({
                "version": "1.0",
                "response": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "No song name was provided."
                    },
                    "shouldEndSession": True
                }
            })
        
        video_id = get_video_id(song_name)
        if not video_id:
            return jsonify({
                "version": "1.0",
                "response": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "I couldn't find the song. Please try again."
                    },
                    "shouldEndSession": True
                }
            })
        
        audio_file = download_audio(video_id)
        if not audio_file:
            return jsonify({
                "version": "1.0",
                "response": {
                    "outputSpeech": {
                        "type": "PlainText",
                        "text": "There was an issue processing the song. Please try again later."
                    },
                    "shouldEndSession": True
                }
            })
        
        audio_url = f"{RENDER_DOMAIN}/static/{video_id}.mp3"
        
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "SSML",
                    "ssml": f"<speak>Playing {song_name} from YouTube Music. <audio src='{audio_url}' /></speak>"
                },
                "shouldEndSession": True
            }
        })
    except Exception as e:
        logging.error(f"Error handling play request: {str(e)}")
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "An unexpected error occurred. Please try again later."
                },
                "shouldEndSession": True
            }
        })

@app.route('/static/<path:filename>')
def serve_audio(filename):
    return send_from_directory('static', filename)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check route to ensure the server is running properly."""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    logging.info("Starting server on port 5000...")
    serve(app, host='0.0.0.0', port=5000)
