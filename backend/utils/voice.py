import requests
import config

BASE = "https://api.elevenlabs.io/v1"


def text_to_speech(text):
    if not config.ELEVEN_API_KEY:
        raise RuntimeError("ELEVEN_API_KEY set nahi hai")
    url = "%s/text-to-speech/%s" % (BASE, config.ELEVEN_VOICE_ID)
    r = requests.post(
        url,
        headers={"xi-api-key": config.ELEVEN_API_KEY},
        json={"text": text[:1500], "model_id": "eleven_multilingual_v2"},
        timeout=60,
    )
    r.raise_for_status()
    return r.content   # mp3 bytes


def speech_to_text(audio_bytes, filename="voice.webm", mimetype="audio/webm"):
    if not config.ELEVEN_API_KEY:
        raise RuntimeError("ELEVEN_API_KEY set nahi hai")
    r = requests.post(
        BASE + "/speech-to-text",
        headers={"xi-api-key": config.ELEVEN_API_KEY},
        data={"model_id": "scribe_v1"},
        files={"file": (filename, audio_bytes, mimetype)},
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("text", "").strip()
