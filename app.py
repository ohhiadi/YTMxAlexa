from flask import Flask, request, jsonify
from flask import Flask, request, jsonify
import yt_dlp
from waitress import serve

app = Flask(__name__)

def get_audio_url(song_name):
    """Fetch the audio URL of a YouTube Music song."""
    ydl_opts = {
        'format': 'bestaudio',
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(song_name, download=False)
        if 'entries' in info and len(info['entries']) > 0:
            return info['entries'][0]['url']
        return None

@app.route('/play', methods=['GET'])
def play_song():
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
    
    audio_url = get_audio_url(song_name)
    if audio_url:
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
    else:
        return jsonify({
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "I couldn't fetch the song. Please try again."
                },
                "shouldEndSession": True
            }
        })

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
