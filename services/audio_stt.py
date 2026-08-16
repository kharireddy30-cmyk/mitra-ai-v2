import os
import re
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range, high_pass_filter, low_pass_filter
import speech_recognition as sr

def apply_audio_dsp(audio_segment: AudioSegment) -> AudioSegment:
    """ఆడియో క్వాలిటీని పెంచే DSP ఫిల్టర్లు"""
    try:
        processed = high_pass_filter(audio_segment, cutoff=300)
        processed = low_pass_filter(processed, cutoff=3800)
        processed = compress_dynamic_range(processed, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
        processed = normalize(processed) + 6.0
        return processed
    except Exception:
        return audio_segment

def transcribe_audio_file(uploaded_audio_file, lang_code="te-IN", enable_dsp=True):
    """సుదీర్ఘమైన ఆడియోలను (5+ నిమిషాలు) 50 సెకన్ల ముక్కలుగా విభజించి పూర్తి టెక్స్ట్‌గా మార్చే ఫంక్షన్"""
    uploaded_audio_file.seek(0)
    file_ext = os.path.splitext(uploaded_audio_file.name)[1].lower()
    if not file_ext:
        file_ext = ".m4a"
        
    temp_in = f"temp_stt_in{file_ext}"
    
    with open(temp_in, "wb") as f:
        f.write(uploaded_audio_file.read())

    full_transcript = []
    recognizer = sr.Recognizer()

    try:
        sound = AudioSegment.from_file(temp_in)
        if enable_dsp:
            sound = apply_audio_dsp(sound)
        
        sound = sound.set_channels(1).set_frame_rate(16000)
        
        # 50 సెకన్ల చొప్పున ఆడియో విభజన (Chunking)
        chunk_length_ms = 50 * 1000
        total_len = len(sound)
        
        for i in range(0, total_len, chunk_length_ms):
            chunk_audio = sound[i:i + chunk_length_ms]
            temp_chunk_wav = f"temp_chunk_{i}.wav"
            chunk_audio.export(temp_chunk_wav, format="wav")
            
            try:
                with sr.AudioFile(temp_chunk_wav) as source:
                    audio_data = recognizer.record(source)
                    part_text = recognizer.recognize_google(audio_data, language=lang_code)
                    if part_text and part_text.strip():
                        full_transcript.append(part_text.strip())
            except sr.UnknownValueError:
                pass
            except Exception:
                pass
            finally:
                if os.path.exists(temp_chunk_wav):
                    os.remove(temp_chunk_wav)

        if full_transcript:
            return " ".join(full_transcript)
        else:
            return "⚠️ Voice not recognized. Check audio language."

    except Exception as e:
        return f"⚠️ STT Error: {e}"
    finally:
        if os.path.exists(temp_in):
            try:
                os.remove(temp_in)
            except Exception:
                pass
