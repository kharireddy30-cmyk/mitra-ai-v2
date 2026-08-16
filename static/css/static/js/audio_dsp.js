// Web Audio DSP & Delta Speech Engine
let audioCtx = null;
let recognition = null;
let isRunning = false;
let globalMasterTranscript = "";
let currentSessionTranscript = "";

function logDiagMessage(msg, type = 'log-info') {
    const consoleEl = document.getElementById('client-diag-console');
    if (!consoleEl) return;
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    const div = document.createElement('div');
    div.className = 'diag-log';
    div.innerHTML = `<span class="log-time">[${time}]</span> <span class="${type}">${msg}</span>`;
    consoleEl.appendChild(div);
    consoleEl.scrollTop = consoleEl.scrollHeight;
}

function initWebAudioDSP(audioElement) {
    if (audioCtx) return;
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AudioContext();
        const source = audioCtx.createMediaElementSource(audioElement);

        const biquadFilter = audioCtx.createBiquadFilter();
        biquadFilter.type = "peaking";
        biquadFilter.frequency.value = 2500;
        biquadFilter.Q.value = 1.2;
        biquadFilter.gain.value = 7.0; // +7dB Vocal Boost

        const compressor = audioCtx.createDynamicsCompressor();
        compressor.threshold.setValueAtTime(-24, audioCtx.currentTime);
        compressor.knee.setValueAtTime(30, audioCtx.currentTime);
        compressor.ratio.setValueAtTime(12, audioCtx.currentTime);
        compressor.attack.setValueAtTime(0.003, audioCtx.currentTime);
        compressor.release.setValueAtTime(0.25, audioCtx.currentTime);

        const gainNode = audioCtx.createGain();
        gainNode.gain.value = 2.5;

        source.connect(biquadFilter);
        biquadFilter.connect(compressor);
        compressor.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        logDiagMessage("✨ Client-side Web Audio DSP పైప్‌లైన్ యాక్టివ్ అయింది (+7dB Peaking @ 2.5kHz, 2.5x Gain)", "log-dsp");
    } catch (e) {
        logDiagMessage(`DSP లోపం: ${e.message}`, "log-err");
    }
}

function startClientSpeechRecognition(langCode = 'te-IN', onTextUpdate) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        logDiagMessage("CRITICAL: బ్రౌజర్‌లో Web Speech API లేదు!", "log-err");
        return null;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = langCode;

    recognition.onstart = () => logDiagMessage("క్లయింట్ స్పీచ్ ఇంజిన్ వాయిస్ సిగ్నల్‌ను గ్రహిస్తోంది.", "log-success");

    recognition.onresult = (event) => {
        let sessionFinal = "";
        let sessionInterim = "";

        for (let i = 0; i < event.results.length; ++i) {
            const text = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                sessionFinal += text.trim() + " ";
            } else {
                sessionInterim += text;
            }
        }

        currentSessionTranscript = (sessionFinal + " " + sessionInterim).trim();
        const fullText = (globalMasterTranscript + " " + currentSessionTranscript).trim();
        if (onTextUpdate) onTextUpdate(fullText);
    };

    recognition.onend = () => {
        if (currentSessionTranscript.trim()) {
            globalMasterTranscript = (globalMasterTranscript + " " + currentSessionTranscript.trim()).trim();
            currentSessionTranscript = "";
        }
        if (isRunning) {
            logDiagMessage("సెషన్ ఆటో-రీస్టార్ట్ అవుతోంది...", "log-action");
            setTimeout(() => {
                if (isRunning) try { recognition.start(); } catch (e) {}
            }, 20);
        }
    };

    recognition.onerror = (e) => {
        logDiagMessage(`స్పీచ్ ఇంజిన్ ఈవెంట్: ${e.error}`, "log-info");
    };

    isRunning = true;
    recognition.start();
    return recognition;
}

function stopClientSpeechRecognition() {
    isRunning = false;
    if (recognition) {
        try { recognition.stop(); } catch (e) {}
    }
    logDiagMessage("స్పీచ్ రికగ్నిషన్ ఆపివేయబడింది.", "log-info");
}
