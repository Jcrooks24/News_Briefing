import logging
import requests

log = logging.getLogger(__name__)

_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def text_to_speech(
    script: str,
    api_key: str,
    voice_id: str,
    model_id: str = "eleven_monolingual_v1",
) -> bytes:
    url = _TTS_URL.format(voice_id=voice_id)
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": script,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }
    log.info("Sending script to ElevenLabs (voice=%s, model=%s)", voice_id, model_id)
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    audio = response.content
    log.info("ElevenLabs returned %d bytes", len(audio))
    return audio
