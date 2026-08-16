import os
import re
import io
import asyncio
import edge_tts
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range, high_pass_filter, low_pass_filter
import speech_recognition as sr
import requests

# 1. Edge-TTS వాయిస్ జనరేటర్
async def generate_voice_file(text, voice, pitch_val, rate_val, output_filename):
    communicate = edge_tts.Communicate(text, voice, pitch=pitch_val, rate=rate_val)
    await communicate.save(output_filename)

# 2. టెక్స్ట్ చంకింగ్ అల్గారిథమ్
def split_text_into_chunks(text, max_chars=300):
    clean_text = re.sub(r'\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?\n।])\s+', clean_text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return [c.strip() for c in chunks if len(c.strip()) > 0]

# 3. పైథాన్ ఆడియో DSP ప్రాసెసర్ (వాయిస్ బూస్టర్ & కంప్రెసర్)
def apply_audio_dsp(audio_segment: AudioSegment) -> AudioSegment:
    """
    మృదువైన, పల్చటి స్త్రీ గొంతులను స్పష్టంగా మార్చే డీప్ ఆడియో DSP పైప్‌లైన్.
    """
    try:
        # A. వోకల్ బ్యాండ్‌పాస్ ఫిల్టర్ (300Hz - 3800Hz)
        processed = high_pass_filter(audio_segment, cutoff=300)
        processed = low_pass_filter(processed, cutoff=3800)

        # B. డైనమిక్స్ కంప్రెసర్ (పల్చటి మాటల వాల్యూమ్‌ను సమానం చేయడం)
        processed = compress_dynamic_range(
            processed, 
            threshold=-20.0, 
            ratio=4.0, 
            attack=5.0, 
            release=50.0
        )

        # C. ఆటో నార్మలైజేషన్ & +6dB గెయిన్ బూస్ట్
        processed = normalize(processed)
        processed = processed + 6.0

        return processed
    except Exception:
        return audio_segment

# 4. డీప్ DSP పవర్డ్ స్పీచ్-టు-టెక్స్ట్ (Audio STT Engine)
def transcribe_audio_file(uploaded_audio_file, lang_code="te-IN", hf_token=None, enable_dsp=True):
    uploaded_audio_file.seek(0)
    temp_in = "temp_stt_in.audio"
    temp_wav = "temp_stt_out.wav"
    
    with open(temp_in, "wb") as f:
        f.write(uploaded_audio_file.read())

    try:
        sound = AudioSegment.from_file(temp_in)

        if enable_dsp:
            sound = apply_audio_dsp(sound)

        # 16kHz మోనో WAV గా ఎక్స్‌పోర్ట్ చేయడం
        sound = sound.set_channels(1).set_frame_rate(16000)
        sound.export(temp_wav, format="wav")

        # HuggingFace Whisper API బ్యాకప్
        if hf_token:
            try:
                with open(temp_wav, "rb") as f_wav:
                    headers = {"Authorization": f"Bearer {hf_token}"}
                    response = requests.post(
                        "https://api-inference.huggingface.co/models/openai/whisper-large-v3",
                        headers=headers,
                        data=f_wav.read(),
                        timeout=30
                    )
                    result = response.json()
                    if "text" in result and result["text"].strip():
                        return result["text"].strip()
            except Exception:
                pass

        # Google Speech Recognition ఇంజిన్
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_wav) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            text_result = recognizer.recognize_google(audio_data, language=lang_code)
            return text_result

    except sr.UnknownValueError:
        return "⚠️ ఆడియోలోని మాటలను ఇంజిన్ గుర్తించలేకపోయింది. దయచేసి స్పష్టమైన ఆడియోను ఎంచుకోండి."
    except Exception as e:
        return f"⚠️ STT ఎర్రర్: {e}"
    finally:
        for p in [temp_in, temp_wav]:
            if os.path.exists(p):
                os.remove(p)
