/**
 * Núcleo de voz — Ronaldo Maestro (TASK-009 v4)
 * STT (Web Speech) · TTS (OpenAI via backend) · conversa fluida
 *
 * Princípios anti-travamento:
 * - Comando só é enviado no FIM da fala (resultado final ou debounce de silêncio),
 *   nunca em resultados interinos — evita cortar o usuário no meio.
 * - Trava `commandInFlight` impede envio duplicado da mesma fala.
 * - Reconhecimento é totalmente parado enquanto o Ronaldo fala (sem eco/feedback).
 */
window.MaestroVoice = (function () {
  const API_BASE = window.location.origin.includes("localhost")
    ? "http://127.0.0.1:8000"
    : window.location.origin;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const sttSupported = Boolean(SpeechRecognition);

  const WAKE_PHRASE = /ronaldo\s+na\s+escuta/i;
  const DIRECT_CMD = /^ronaldo[,:\s]+(.+)/i;
  const WAKE_ACK = "Pode falar.";
  const SILENCE_MS = 1000; // pausa que marca fim de fala

  let cfg = {};
  let recognition = null;
  let listening = false;
  let engineRunning = false; // true entre onstart e onend (motor STT ativo)
  let speaking = false;
  let processing = false;
  let plantaoActive = false;
  let awaitingCommand = false;
  let commandInFlight = false;
  let listenMode = "manual"; // manual | plantao | command
  let finalText = "";
  let interimText = "";
  let silenceTimer = null;
  let restartTimer = null;

  const els = {};
  const $ = (id) => document.getElementById(id);

  function bindEls() {
    els.overlay = $("voice-overlay");
    els.btnVoice = $("btn-voice");
    els.btnToggle = $("voice-toggle");
    els.btnClose = $("voice-close");
    els.status = $("voice-status");
    els.ring = $("voice-ring");
    els.stateDot = $("plantao-state-dot");
    els.stateLabel = $("plantao-state-label");
  }

  // ---- UI -----------------------------------------------------------------
  function setState(state) {
    if (els.stateDot) els.stateDot.dataset.state = state;
    if (els.stateLabel) {
      const labels = {
        idle: "Aguardando",
        listening: "Ouvindo",
        processing: "Pensando",
        speaking: "Ronaldo falando",
      };
      els.stateLabel.textContent = labels[state] || state;
    }
    document.body?.classList.toggle("voice-speaking", state === "speaking");
    document.body?.classList.toggle("voice-listening", state === "listening");
    document.body?.classList.toggle("voice-processing", state === "processing");
  }

  function updateStatus(extra) {
    if (!els.status) return;
    if (extra) { els.status.textContent = extra; return; }
    if (speaking) els.status.textContent = "Ronaldo falando…";
    else if (processing) els.status.textContent = "Pensando…";
    else if (listening && awaitingCommand) els.status.textContent = "Pode falar";
    else if (listening) els.status.textContent = "Ouvindo…";
    else if (plantaoActive) els.status.textContent = "Escuta ativa";
    else els.status.textContent = sttSupported ? "Toque para falar" : "Voz não suportada";
  }

  function reflectListening(on) {
    listening = on;
    els.btnVoice?.classList.toggle("listening", on && !plantaoActive);
    els.ring?.classList.toggle("active", on);
    if (els.btnToggle) els.btnToggle.textContent = on ? "⏹ Parar" : "🎤 Falar";
    if (!speaking && !processing) setState(on ? "listening" : "idle");
    updateStatus();
  }

  // ---- Reconhecimento -----------------------------------------------------
  function clearSilence() {
    if (silenceTimer) { clearTimeout(silenceTimer); silenceTimer = null; }
  }

  function clearRestart() {
    if (restartTimer) { clearTimeout(restartTimer); restartTimer = null; }
  }

  function resetTranscript() {
    finalText = "";
    interimText = "";
    clearSilence();
  }

  function stopListening() {
    clearSilence();
    clearRestart();
    if (recognition) {
      try { recognition.abort(); } catch (_) { /* noop */ }
    }
    reflectListening(false);
  }

  /**
   * Fonte única de reinício da escuta no Plantão. Evita corridas de múltiplos
   * `start()` simultâneos (a causa das falhas entre uma pergunta e outra).
   */
  function armListening(delay = 300) {
    clearRestart();
    if (!plantaoActive) return;
    restartTimer = setTimeout(() => {
      restartTimer = null;
      if (!plantaoActive || speaking || processing || engineRunning) return;
      if (awaitingCommand) startCommandListening();
      else startPlantaoListening();
    }, delay);
  }

  function commitUtterance() {
    clearSilence();
    const text = (finalText || interimText || "").trim();
    if (text.length < 3) return;
    // Para o reconhecimento antes de agir (evita captar a própria resposta).
    stopListening();
    handleTranscript(text);
  }

  function scheduleSilenceCommit() {
    clearSilence();
    silenceTimer = setTimeout(commitUtterance, SILENCE_MS);
  }

  function initRecognition(continuous) {
    if (!sttSupported) return null;
    const rec = new SpeechRecognition();
    rec.lang = "pt-BR";
    rec.continuous = continuous;
    rec.interimResults = true;
    rec.maxAlternatives = 1;

    rec.onstart = () => {
      engineRunning = true;
      resetTranscript();
      reflectListening(true);
    };

    rec.onresult = (event) => {
      if (speaking || processing) return;
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const seg = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += seg + " ";
        else interim += seg;
      }
      interimText = interim;

      // Wake word: responde já no interino (frase curta), sem esperar silêncio.
      if ((listenMode === "plantao" || listenMode === "command") && !awaitingCommand) {
        const probe = (finalText || interim).trim();
        if (WAKE_PHRASE.test(probe) && probe.replace(WAKE_PHRASE, "").trim().length < 4) {
          commitUtterance();
          return;
        }
      }

      // Comando: só fecha no resultado final ou após pausa de silêncio.
      const hasFinal = finalText.trim().length >= 3 && !interim;
      if (hasFinal) commitUtterance();
      else scheduleSilenceCommit();
    };

    rec.onerror = (event) => {
      if (event.error === "no-speech" || event.error === "aborted") return;
      updateStatus(event.error === "not-allowed" ? "Permita o microfone" : `Erro: ${event.error}`);
      reflectListening(false);
    };

    rec.onend = () => {
      engineRunning = false;
      reflectListening(false);
      if (speaking || processing) return;

      // Manual: se sobrou fala não confirmada, confirma agora.
      if (listenMode === "manual") {
        const text = (finalText || interimText || "").trim();
        if (text.length >= 3 && !commandInFlight) handleTranscript(text);
        return;
      }

      // Plantão: re-arma a escuta por uma única fonte (sem corridas).
      if (plantaoActive) armListening(350);
    };

    return rec;
  }

  function startRecognition(continuous, mode) {
    if (!sttSupported || speaking || processing) return;
    listenMode = mode;
    // Se o motor ainda está rodando, não chama start() de novo (evita
    // InvalidStateError); o onend vai re-armar quando encerrar.
    if (engineRunning) {
      try { recognition.abort(); } catch (_) { /* noop */ }
      armListening(300);
      return;
    }
    recognition = initRecognition(continuous);
    resetTranscript();
    try {
      recognition.start();
    } catch (_) {
      engineRunning = false;
      armListening(300);
    }
  }

  function startListening() {
    if (!sttSupported) { updateStatus("Use Chrome ou Edge"); return; }
    if (plantaoActive) stopListening();
    startRecognition(false, "manual");
  }

  function startPlantaoListening() {
    if (!plantaoActive || !sttSupported) return;
    startRecognition(true, "plantao");
  }

  function startCommandListening() {
    if (!sttSupported) return;
    startRecognition(false, "command");
  }

  // ---- Interpretação ------------------------------------------------------
  function parseUtterance(text) {
    const t = text.trim();
    if (!t) return null;

    if (WAKE_PHRASE.test(t) && t.replace(WAKE_PHRASE, "").trim().length < 4) {
      return { type: "wake" };
    }
    const direct = t.match(DIRECT_CMD);
    if (direct) return { type: "command", command: direct[1].trim() || t };
    if (awaitingCommand && t.length >= 3) return { type: "command", command: t };
    if (plantaoActive && WAKE_PHRASE.test(t)) {
      const rest = t.replace(WAKE_PHRASE, "").replace(/^[,:\s]+/, "").trim();
      return rest.length >= 3 ? { type: "command", command: rest } : { type: "wake" };
    }
    return null;
  }

  function handleTranscript(text) {
    if (commandInFlight) return false;
    const parsed = parseUtterance(text);
    if (!parsed) {
      // Em modo manual, qualquer fala vira comando.
      if (listenMode === "manual" && text.trim().length >= 3) {
        sendCommand(text.trim());
        return true;
      }
      return false;
    }

    if (parsed.type === "wake") {
      awaitingCommand = true;
      updateStatus("Pode falar");
      speakText(WAKE_ACK).then(() => {
        if (plantaoActive) armListening(200);
        else startCommandListening();
      });
      return true;
    }

    if (parsed.type === "command" && parsed.command.length >= 3) {
      awaitingCommand = false;
      sendCommand(parsed.command);
      return true;
    }
    return false;
  }

  // ---- TTS ----------------------------------------------------------------
  let currentAudio = null;

  function stopAudio() {
    if (currentAudio) { currentAudio.pause(); currentAudio = null; }
    if ("speechSynthesis" in window) speechSynthesis.cancel();
  }

  function cleanForSpeech(text) {
    return text
      .replace(/TASK[-\s]?(\d+)/gi, (_, n) => `tarefa ${n}`)
      .replace(/\bWIP\b/gi, "tarefas em andamento")
      .replace(/\bVPS\b/gi, "servidor")
      .replace(/^[-•*]\s+/gm, "")
      .replace(/\n+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function speechTextFromResponse(data) {
    return cleanForSpeech(data.reply_speech || data.reply || "");
  }

  function playBlob(blob) {
    return new Promise((resolve) => {
      stopAudio();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      currentAudio = audio;
      const done = () => { URL.revokeObjectURL(url); currentAudio = null; resolve(); };
      audio.onended = done;
      audio.onerror = done;
      audio.play().catch(done);
    });
  }

  function speakBrowserFallback(text) {
    if (!("speechSynthesis" in window) || !text) return Promise.resolve();
    return new Promise((resolve) => {
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "pt-BR";
      u.onend = resolve;
      u.onerror = resolve;
      speechSynthesis.speak(u);
    });
  }

  async function speakText(text) {
    if (!text) return;
    speaking = true;
    setState("speaking");
    updateStatus();
    try {
      const res = await fetch(`${API_BASE}/api/maestro/ronaldo/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (res.ok) await playBlob(await res.blob());
      else await speakBrowserFallback(text);
    } catch (_) {
      await speakBrowserFallback(text);
    } finally {
      speaking = false;
      setState("idle");
      updateStatus();
    }
  }

  // ---- Comando ------------------------------------------------------------
  async function sendCommand(text) {
    if (commandInFlight) return;
    commandInFlight = true;
    processing = true;
    setState("processing");
    updateStatus();
    if (els.btnToggle) els.btnToggle.disabled = true;

    try {
      const res = await fetch(`${API_BASE}/api/maestro/ronaldo/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: text }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      cfg.onSuccess?.(data);
      await speakText(speechTextFromResponse(data));
      cfg.onAfterSpeak?.(data);
    } catch (err) {
      updateStatus(`Falha: ${err.message}`);
      cfg.onError?.(err);
    } finally {
      processing = false;
      commandInFlight = false;
      if (els.btnToggle) els.btnToggle.disabled = !sttSupported;
      updateStatus();
      if (plantaoActive) {
        awaitingCommand = false;
        armListening(450);
      }
    }
  }

  // ---- Painel/overlay -----------------------------------------------------
  function openPanel() {
    els.overlay?.classList.remove("hidden");
    updateStatus();
    if (els.btnToggle) els.btnToggle.disabled = !sttSupported || processing;
  }

  function closePanel() {
    if (plantaoActive) return;
    els.overlay?.classList.add("hidden");
    stopListening();
    stopAudio();
  }

  function startPlantao() {
    plantaoActive = true;
    awaitingCommand = false;
    setState("idle");
    updateStatus();
    startPlantaoListening();
  }

  function stopPlantao() {
    plantaoActive = false;
    awaitingCommand = false;
    stopListening();
    stopAudio();
    setState("idle");
    updateStatus();
  }

  function bindDashboard() {
    els.btnVoice?.addEventListener("click", () => { openPanel(); startListening(); });
    els.btnToggle?.addEventListener("click", () => {
      if (listening) stopListening();
      else startListening();
    });
    els.btnClose?.addEventListener("click", closePanel);
    els.overlay?.addEventListener("click", (e) => {
      if (e.target === els.overlay) closePanel();
    });
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === "m") {
        e.preventDefault();
        if (els.overlay?.classList.contains("hidden")) { openPanel(); startListening(); }
        else if (listening) stopListening();
        else startListening();
      }
      if (e.key === "Escape" && !els.overlay?.classList.contains("hidden")) closePanel();
    });
  }

  function init(options = {}) {
    cfg = options;
    bindEls();
    if (cfg.mode === "plantao") {
      startPlantao();
      window.addEventListener("beforeunload", stopPlantao);
      return;
    }
    localStorage.removeItem("maestro_plantao");
    bindDashboard();
  }

  return { init, startPlantao, stopPlantao, speakText, closePanel };
})();
