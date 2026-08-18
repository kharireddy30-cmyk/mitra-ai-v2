import os
import io
import re
import asyncio
import edge_tts
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range, high_pass_filter, low_pass_filter
import speech_recognition as sr

def detect_chunk_language(text):
    te_count = len(re.findall(r'[\u0C00-\u0C7F]', text))
    hi_count = len(re.findall(r'[\u0900-\u097F]', text))
    en_count = len(re.findall(r'[a-zA-Z]', text))

    if te_count > hi_count and te_count > en_count:
        return "te"
    elif hi_count > te_count and hi_count > en_count:
        return "hi"
    elif en_count > 0:
        return "en"
    return "te"

def apply_audio_dsp(audio_segment: AudioSegment) -> AudioSegment:
    try:
        processed = high_pass_filter(audio_segment, cutoff=300)
        processed = low_pass_filter(processed, cutoff=3800)
        processed = compress_dynamic_range(processed, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
        processed = normalize(processed) + 6.0
        return processed
    except Exception:
        return audio_segment

def transcribe_audio_file(uploaded_audio_file, lang_code="auto", enable_dsp=True):
    uploaded_audio_file.seek(0)
    file_ext = os.path.splitext(uploaded_audio_file.name)[1].lower() or ".m4a"
        
    temp_in = f"temp_stt_in{file_ext}"
    with open(temp_in, "wb") as f:
        f.write(uploaded_audio_file.read())

    full_transcript = []
    recognizer = sr.Recognizer()
    target_langs = ["te-IN", "hi-IN", "en-IN"] if lang_code == "auto" else [lang_code]

    try:
        sound = AudioSegment.from_file(temp_in)
        if enable_dsp:
            sound = apply_audio_dsp(sound)
        
        sound = sound.set_channels(1).set_frame_rate(16000)
        chunk_length_ms = 45 * 1000
        total_len = len(sound)
        
        for i in range(0, total_len, chunk_length_ms):
            chunk_audio = sound[i:i + chunk_length_ms]
            temp_chunk_wav = f"temp_chunk_{i}.wav"
            chunk_audio.export(temp_chunk_wav, format="wav")
            
            for test_lang in target_langs:
                try:
                    with sr.AudioFile(temp_chunk_wav) as source:
                        audio_data = recognizer.record(source)
                        part_text = recognizer.recognize_google(audio_data, language=test_lang)
                        if part_text and part_text.strip():
                            full_transcript.append(part_text.strip())
                            break
                except Exception:
                    continue
            
            if os.path.exists(temp_chunk_wav):
                try:
                    os.remove(temp_chunk_wav)
                except Exception:
                    pass

        if full_transcript:
            return " ".join(full_transcript)
        else:
            return "⚠️ Voice not recognized. Try selecting a specific language."
    except Exception as e:
        return f"⚠️ STT Error: {e}"
    finally:
        if os.path.exists(temp_in):
            try:
                os.remove(temp_in)
            except Exception:
                pass

async def generate_voice_chunk(text, voice, pitch_val, rate_val, output_filename):
    communicate = edge_tts.Communicate(text, voice, pitch=pitch_val, rate=rate_val)
    await communicate.save(output_filename)

def split_text_into_chunks(text, max_chars=200):
    clean_text = re.sub(r'[\r]+', '', text).strip()
    if not clean_text:
        return []
    raw_sentences = re.split(r'(?<=[.!?\n।])\s+|(?<=\.\.\.)\s+', clean_text)
    chunks = []
    for sentence in raw_sentences:
        s_clean = sentence.strip()
        if not s_clean:
            continue
        if len(s_clean) <= max_chars:
            chunks.append(s_clean)
        else:
            words = s_clean.split(' ')
            curr_chunk = ""
            for word in words:
                if len(curr_chunk) + len(word) + 1 <= max_chars:
                    curr_chunk += word + " "
                else:
                    if curr_chunk.strip():
                        chunks.append(curr_chunk.strip())
                    curr_chunk = word + " "
            if curr_chunk.strip():
                chunks.append(curr_chunk.strip())
    return [c.strip() for c in chunks if len(c.strip()) > 0]

def synthesize_multilang_tts(text, tts_mode, gender, speed, pitch_custom, pause_sec, enable_bgm, bgm_vol):
    clean_txt = re.sub(r'[*#_~`]', '', text)
    rate_str = f"{int((speed - 1.0) * 100):+d}%"
    pitch_val_map = {"Normal": "+0Hz", "Deep Base": "-5Hz", "Heavy Base": "-10Hz"}
    pitch_str = pitch_val_map.get(pitch_custom, "+0Hz")

    voice_dict = {
        "te": "te-IN-MohanNeural" if "Male" in gender else "te-IN-ShrutiNeural",
        "hi": "hi-IN-MadhurNeural" if "Male" in gender else "hi-IN-SwaraNeural",
        "en": "en-IN-PrabhatNeural" if "Male" in gender else "en-IN-NeerjaNeural"
    }

    text_chunks = split_text_into_chunks(clean_txt, max_chars=200)
    speech_sound = AudioSegment.empty()
    silence_pause = AudioSegment.silent(duration=int(pause_sec * 1000))

    for i, chunk in enumerate(text_chunks):
        if "Auto" in tts_mode:
            detected_l = detect_chunk_language(chunk)
            chosen_voice = voice_dict[detected_l]
        elif "Telugu" in tts_mode:
            chosen_voice = voice_dict["te"]
        elif "Hindi" in tts_mode:
            chosen_voice = voice_dict["hi"]
        else:
            chosen_voice = voice_dict["en"]

        temp_file = f"temp_tts_{i}.mp3"
        try:
            asyncio.run(generate_voice_chunk(chunk, chosen_voice, pitch_str, rate_str, temp_file))
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                chunk_sound = AudioSegment.from_file(temp_file)
                speech_sound += chunk_sound + silence_pause
                os.remove(temp_file)
        except Exception:
            pass

    if len(speech_sound) > 0:
        final_sound = speech_sound
        if enable_bgm and os.path.exists("bgm.mp3"):
            try:
                bgm_sound = AudioSegment.from_file("bgm.mp3")
                if len(bgm_sound) < len(speech_sound):
                    bgm_sound = bgm_sound * ((len(speech_sound) // len(bgm_sound)) + 1)
                bgm_sound = bgm_sound[:len(speech_sound) + 1000]
                reduction_db = 22 - (bgm_vol * 1.5)
                bgm_sound = bgm_sound - reduction_db
                final_sound = speech_sound.overlay(bgm_sound)
            except Exception:
                pass

        final_fp = io.BytesIO()
        final_sound.export(final_fp, format="mp3")
        return final_fp.getvalue()
    return None
