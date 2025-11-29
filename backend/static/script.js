document.addEventListener("DOMContentLoaded", () => {
  const uploadForm = document.getElementById("upload-form");
  const fileInput = document.getElementById("file-input");
  const loading = document.getElementById("loading");
  const summaryText = document.getElementById("summaryText");
  const translateBtn = document.getElementById("translate-btn");
  const languageSelect = document.getElementById("language-select");
  const translatedTextDiv = document.getElementById("translated-text");
  const speakBtn = document.getElementById("speak-btn");
  const stopBtn = document.getElementById("stop-btn");

  let currentText = "";
  let audio = null;

  // ===============================
  // 📄 Upload & Explain Document
  // ===============================
  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!fileInput.files.length) {
      alert("📄 Please select a .docx file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    loading.style.display = "block";
    summaryText.textContent = "";

    try {
      const response = await fetch("/process-doc", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      loading.style.display = "none";

      if (response.ok) {
        summaryText.textContent = data.summary;
        currentText = data.summary;
      } else {
        alert(`❌ Error: ${data.error || "Failed to process document"}`);
      }
    } catch (error) {
      loading.style.display = "none";
      alert("⚠️ Network error while processing document.");
      console.error(error);
    }
  });

  // ===============================
  // 🌐 Translate Summary
  // ===============================
  translateBtn.addEventListener("click", async () => {
    const text = currentText;
    const targetLang = languageSelect.value;

    if (!text) {
      alert("📄 Please upload and process a document first.");
      return;
    }
    if (!targetLang) {
      alert("🌐 Please select a language.");
      return;
    }

    translatedTextDiv.textContent = "Translating... ⏳";

    try {
      const response = await fetch("/translate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, target_lang: targetLang }),
      });

      const data = await response.json();
      if (response.ok) {
        translatedTextDiv.textContent = data.translated_text;
        currentText = data.translated_text;
      } else {
        translatedTextDiv.textContent = `❌ ${data.error}`;
      }
    } catch (error) {
      translatedTextDiv.textContent = "⚠️ Translation failed.";
      console.error(error);
    }
  });

  // ===============================
  // 🎧 Human-like Read Aloud (Edge TTS)
  // ===============================
  speakBtn.addEventListener("click", async () => {
    const textToRead =
      document.getElementById("translated-text").textContent.trim() ||
      document.getElementById("summaryText").textContent.trim();
    const targetLang = document.getElementById("language-select").value || "en";

    if (!textToRead) {
      alert("Please summarize or translate text first.");
      return;
    }

    speakBtn.disabled = true;
    speakBtn.textContent = "🎧 Generating Voice...";

    try {
      const response = await fetch("/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textToRead, lang: targetLang }),
      });

      const data = await response.json();
      speakBtn.disabled = false;
      speakBtn.textContent = "🎧 Read Aloud";

      if (response.ok && data.audio_url) {
        // Stop previous audio if playing
        if (audio) {
          audio.pause();
          audio.currentTime = 0;
        }

        // Start new playback
        audio = new Audio(data.audio_url);
        audio.volume = 1.0;
        audio.play()
          .then(() => console.log("🎵 Voice playback started."))
          .catch((err) => console.error("🔇 Playback error:", err));
      } else {
        alert("❌ TTS failed: " + (data.error || "Unknown error"));
      }
    } catch (err) {
      speakBtn.disabled = false;
      speakBtn.textContent = "🎧 Read Aloud";
      console.error("⚠️ TTS Error:", err);
      alert("TTS request failed. Check connection or server logs.");
    }
  });

  // 🛑 Stop Playback
  stopBtn.addEventListener("click", () => {
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
      console.log("⏹️ Stopped audio playback.");
    }
  });

 

 
});
