import os
import requests
from typing import Dict, Any, Optional

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_INSTANCE_ID = os.getenv("EVOLUTION_INSTANCE_ID")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")  # header 'apikey'

def parse_evolution_event(body: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Return a parsed WhatsApp message in the form:
    { 'chat_id': str, 'number': str, 'type': str, 'message': str, 'media_url': Optional[str] }
    """
    try:
        event = body.get("event") or body.get("type")
        data = body.get("data") or body
        if not data:
            return None

        # Sender info
        remote_jid = data.get("key", {}).get("remoteJid") or data.get("remoteJid")
        if not remote_jid:
            return None

        number = remote_jid.split("@")[0]
        chat_id = number

        # Message object
        msg_obj = data.get("message") or {}

        # Route depending on type
        if "conversation" in msg_obj or "extendedTextMessage" in msg_obj:
            return _parse_text(chat_id, number, msg_obj)

        elif "audioMessage" in msg_obj:
            return _parse_audio(chat_id, number, msg_obj)

        else:
            return None  # unhandled type

    except Exception as e:
        print(f"parse_evolution_event error: {e}")
        return None


def _parse_text(chat_id: str, number: str, msg_obj: Dict[str, Any]) -> Dict[str, str]:
    text = (
        msg_obj.get("conversation")
        or msg_obj.get("extendedTextMessage", {}).get("text")
    )
    return {"chat_id": chat_id, "number": number, "type": "text", "message": text}

# from transformers import pipeline
# # Load once at startup
# asr = pipeline("automatic-speech-recognition", model="openai/whisper-small")
# def _transcribe_audio(file_path: str) -> str:
#     result = asr(file_path)
#     return result["text"]

def _transcribe_audio(file_path: str) -> str:
    return f"Pending transcribing: {file_path}"

def _parse_audio(chat_id: str, number: str, msg_obj: Dict[str, Any]) -> Dict[str, str]:
    """
    For audio messages, WhatsApp typically provides a mediaKey + direct download URL.
    You’ll usually need to fetch the audio file via Evolution API’s media endpoint.
    """
    audio = msg_obj.get("audioMessage", {})
    media_url = audio.get("url") or audio.get("directPath")
    # mime_type = audio.get("mimetype")

    text = _transcribe_audio(media_url)

    return {
        "chat_id": chat_id,
        "number": number,
        "type": "audio",
        "message": text
        # "message": "",  # will be filled once transcribed
        # "media_url": media_url,
        # "mime_type": mime_type,
    }

import time
from typing import Literal, Optional

def send_evolution_presence(
    number: str,
    presence: Literal["composing", "recording", "paused", "available", "unavailable"] = "composing",
    duration_ms: Optional[int] = None
    ) -> None:
    """
    Sends a presence update (typing/recording/paused/available/unavailable) via Evolution API.
    - presence values (Baileys-compatible):
    * composing   -> typing
    * recording   -> audio recording
    * paused      -> stop typing/recording
    * available   -> online
    * unavailable -> offline

    If duration_ms is provided and presence is 'composing' or 'recording',
    this will:
    1) send the presence
    2) wait for duration_ms
    3) send a 'paused' presence

    Body: {
        "number": "55xxxxxxxxxx",
        "options": {
            "delay": 500,
            "presence": "composing",
            "number": "55xxxxxxxxxx"
        }
    }
    """
    if not (EVOLUTION_API_URL and EVOLUTION_INSTANCE_ID and EVOLUTION_API_KEY):
        print("Evolution API config missing; cannot send presence.")
        return

    url = f"{EVOLUTION_API_URL}/chat/sendPresence/{EVOLUTION_INSTANCE_ID}"
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}

    def _post(pres: str):
        payload = {"number": number, "presence": pres}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"Failed to send Evolution presence '{pres}': {e}")

    # Send initial presence
    _post(presence)

    # Optional auto-stop after a duration
    if duration_ms and presence in ("composing", "recording"):
        try:
            time.sleep(max(duration_ms, 0) / 1000.0)
        finally:
            _post("paused")

def send_evolution_text(number: str, text: str) -> None:
    """
    Sends a text message back via Evolution API.
    Default path for many Evolution setups: POST /message/sendText/{instanceId}
    Body: { "number": "55xxxxxxxxxx", "text": "..." }
    """
    if not (EVOLUTION_API_URL and EVOLUTION_INSTANCE_ID and EVOLUTION_API_KEY):
        print("Evolution API config missing; cannot send message.")
        return
    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE_ID}"
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
    payload = {"number": number, "text": text}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to send Evolution message: {e}")
