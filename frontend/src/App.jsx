import React, { useEffect, useState } from 'react';
import './index.css';
import { translations } from './translations';

function readPref(key, fallback) {
  try {
    return localStorage.getItem(key) || fallback;
  } catch {
    return fallback;
  }
}

const PILL_TAGS = [
  '🟡 Yellow round',
  '⚪ White round',
  '🔴 Red capsule',
  '🔵 Blue capsule',
  '🥄 Liquid syrup',
  '🟢 Green oval'
];

export default function App() {
  const [step, setStep] = useState('upload'); // 'upload' | 'verify' | 'schedule'
  const [selectedFile, setSelectedFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [language, setLanguage] = useState(() => readPref('msa-lang', 'en'));
  const [textSize, setTextSize] = useState(() => readPref('msa-text', 'large'));
  const [highContrast, setHighContrast] = useState(() => readPref('msa-contrast', 'off') === 'on');
  const t = translations[language] || translations['en'];

  useEffect(() => {
    document.documentElement.lang = language === 'hi' ? 'hi' : 'en';
    try {
      localStorage.setItem('msa-lang', language);
      localStorage.setItem('msa-text', textSize);
      localStorage.setItem('msa-contrast', highContrast ? 'on' : 'off');
    } catch {
      /* ignore private-mode storage errors */
    }
  }, [language, textSize, highContrast]);

  const [extractedMeds, setExtractedMeds] = useState([]);
  const [unreadableRegions, setUnreadableRegions] = useState([]);
  const [scheduleData, setScheduleData] = useState(null);
  const [interactions, setInteractions] = useState([]);
  const [spokenGuide, setSpokenGuide] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [qaInput, setQaInput] = useState('');
  const [qaAnswer, setQaAnswer] = useState('');
  const [isListening, setIsListening] = useState(false);

  const speakText = (text) => {
    if (!('speechSynthesis' in window)) {
      alert("Text-to-speech is not supported in this browser.");
      return;
    }
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const langCodeMap = { en: 'en-US', hi: 'hi-IN' };
    utterance.lang = langCodeMap[language] || 'en-US';
    const voices = window.speechSynthesis.getVoices();
    const matchedVoice = voices.find(v => v.lang.startsWith(language) || v.lang.replace('_', '-').startsWith(language));
    if (matchedVoice) utterance.voice = matchedVoice;
    utterance.rate = 0.88;
    utterance.pitch = 1.0;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const startVoiceInput = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice input is not supported in this browser. Please type your question.");
      return;
    }
    const recognition = new SpeechRecognition();
    const langCodeMap = { en: 'en-US', hi: 'hi-IN' };
    recognition.lang = langCodeMap[language] || 'en-US';
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setQaInput(transcript);
      handleAskQuestion(transcript);
    };
    recognition.start();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleLoadSample = async (samplePath) => {
    try {
      setLoading(true);
      setLoadingMessage(t.readingPrescription);
      setImagePreview(samplePath);
      const response = await fetch(samplePath);
      const blob = await response.blob();
      const file = new File([blob], "sample_prescription.png", { type: "image/png" });
      setSelectedFile(file);
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/extract/prescription', { method: 'POST', body: formData });
      if (!res.ok) throw new Error("Failed to extract prescription");
      const data = await res.json();
      setExtractedMeds(data.medicines || []);
      setUnreadableRegions(data.unreadable_regions || []);
      setStep('verify');
    } catch (err) {
      alert("Error loading sample: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExtract = async () => {
    if (!selectedFile) return;
    setLoading(true);
    setLoadingMessage(t.readingPrescription);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      const res = await fetch('/api/extract/prescription', { method: 'POST', body: formData });
      if (!res.ok) throw new Error("Failed to extract prescription");
      const data = await res.json();
      setExtractedMeds(data.medicines || []);
      setUnreadableRegions(data.unreadable_regions || []);
      if (data.language_detected && language === 'en' && data.language_detected !== 'en') {
        setLanguage(data.language_detected);
      }
      setStep('verify');
    } catch (err) {
      alert("Error reading prescription: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMedChange = (index, field, value) => {
    const updated = [...extractedMeds];
    updated[index][field] = value;
    updated[index].confidence = 1.0;
    setExtractedMeds(updated);
  };

  const handleRemoveMed = (index) => {
    setExtractedMeds(extractedMeds.filter((_, i) => i !== index));
  };

  const handleAddMed = () => {
    setExtractedMeds([
      ...extractedMeds,
      {
        name: '',
        strength: '',
        frequency_raw: 'OD',
        duration: '',
        instructions: 'after meals',
        source_text: 'Manual entry',
        confidence: 1.0
      }
    ]);
  };

  const handleLanguageChange = async (newLang) => {
    setLanguage(newLang);
    if (step === 'schedule' && extractedMeds.length > 0) {
      setLoading(true);
      setLoadingMessage(`Translating routine into ${translations[newLang]?.appTitle || newLang}...`);
      try {
        const res = await fetch('/api/process-confirmed', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ confirmed_medicines: extractedMeds, language: newLang })
        });
        if (res.ok) {
          const data = await res.json();
          setSpokenGuide(data.spoken_explanation || '');
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleConfirmAndProcess = async () => {
    setLoading(true);
    setLoadingMessage(t.calculatingSchedule);
    try {
      const res = await fetch('/api/process-confirmed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirmed_medicines: extractedMeds, language: language })
      });
      if (!res.ok) throw new Error("Processing failed");
      const data = await res.json();
      setScheduleData(data.schedule);
      setInteractions(data.interactions || []);
      setSpokenGuide(data.spoken_explanation || '');
      setStep('schedule');
    } catch (err) {
      alert("Error generating schedule: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async (qText) => {
    const question = qText || qaInput;
    if (!question.trim()) return;
    setLoading(true);
    setLoadingMessage(t.answeringQuestion);
    try {
      const res = await fetch('/api/qa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question,
          confirmed_medicines: extractedMeds,
          language: language
        })
      });
      const data = await res.json();
      setQaAnswer(data.answer);
      speakText(data.answer);
    } catch (err) {
      alert("Error answering question: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const stepClass = (name) => {
    if (step === name) return 'step-item active';
    if (name === 'upload') return 'step-item completed';
    if (name === 'verify' && step === 'schedule') return 'step-item completed';
    return 'step-item';
  };

  const renderDose = (d, i) => (
    <div key={i} className="dose-item">
      <div className="dose-name">{d.medicine_name} {d.strength || ''}</div>
      <div className="dose-instructions">
        {d.meal_relation.replace('_', ' ')} {d.instructions ? `• ${d.instructions}` : ''}
      </div>
      {d.pill_visual && (
        <div className="pill-visual-badge">
          <span>{d.pill_visual}</span>
        </div>
      )}
    </div>
  );

  return (
    <div className={`app-shell text-${textSize}${highContrast ? ' contrast-high' : ''}`}>
      <div className="app-container">
        <a className="skip-link" href="#main-content">{t.skipToContent}</a>
        <header className="app-header">
          <div className="brand-row">
            <div className="brand-mark" aria-hidden="true">💊</div>
            <div>
              <h1 className="brand-title">{t.appTitle.replace(/^💊\s*/, '')}</h1>
              <p className="tagline">{t.tagline}</p>
            </div>
          </div>
          <div className="a11y-bar">
            <div className="control-block">
              <div className="control-label" id="lang-label">{t.langLabel}</div>
              <div className="seg-group" role="group" aria-labelledby="lang-label">
                <button type="button" className={`seg-btn ${language === 'en' ? 'active' : ''}`} onClick={() => handleLanguageChange('en')} aria-pressed={language === 'en'}>English</button>
                <button type="button" className={`seg-btn ${language === 'hi' ? 'active' : ''}`} onClick={() => handleLanguageChange('hi')} aria-pressed={language === 'hi'}>हिंदी</button>
              </div>
            </div>
            <div className="control-block">
              <div className="control-label" id="contrast-label">{t.contrastLabel}</div>
              <div className="seg-group" role="group" aria-labelledby="contrast-label">
                <button type="button" className={`seg-btn ${!highContrast ? 'active' : ''}`} onClick={() => setHighContrast(false)} aria-pressed={!highContrast}>{t.contrastOff}</button>
                <button type="button" className={`seg-btn ${highContrast ? 'active' : ''}`} onClick={() => setHighContrast(true)} aria-pressed={highContrast}>{t.contrastOn}</button>
              </div>
            </div>
          </div>
        </header>

        <nav className="step-banner" aria-label="Progress">
          <div className={stepClass('upload')}>
            <span className="step-num">1</span>
            <span>{t.stepPhoto}</span>
          </div>
          <div className={stepClass('verify')}>
            <span className="step-num">2</span>
            <span>{t.stepVerify}</span>
          </div>
          <div className={stepClass('schedule')}>
            <span className="step-num">3</span>
            <span>{t.stepSchedule}</span>
          </div>
        </nav>

        {loading && (
          <div className="loading-banner" role="status" aria-live="polite">
            ⏳ {loadingMessage}
          </div>
        )}

        <main id="main-content">
        {step === 'upload' && (
          <div className="stack">
            <div
              className="upload-card"
              role="button"
              tabIndex={0}
              onClick={() => document.getElementById('rxInput').click()}
              onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && document.getElementById('rxInput').click()}
            >
              <input
                id="rxInput"
                type="file"
                accept="image/*"
                capture="environment"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              <div className="upload-icon">📸</div>
              <h2>{t.takePhoto}</h2>
              <p className="hint">{t.tapToSnap}</p>
            </div>

            {imagePreview && (
              <div className="preview-wrap">
                <img src={imagePreview} alt="Prescription Preview" className="camera-preview" />
                <div>
                  <button className="btn btn-primary" onClick={handleExtract}>
                    {t.readPrescriptionSafely}
                  </button>
                </div>
              </div>
            )}

            <div className="panel">
              <h3>{t.orTrySample}</h3>
              <div className="sample-list">
                <button className="sample-pill-btn" onClick={() => handleLoadSample('/samples/synthetic_rx_1.png')}>
                  💊 {t.sample1}
                </button>
                <button className="sample-pill-btn" onClick={() => handleLoadSample('/samples/fever_cough_rx.png')}>
                  🌡️ {t.sample2}
                </button>
                <button className="sample-pill-btn" onClick={() => handleLoadSample('/samples/pain_conflict_rx.png')}>
                  ⚠️ {t.sample3}
                </button>
              </div>
            </div>
          </div>
        )}

        {step === 'verify' && (
          <div className="stack">
            <div className="notice notice-warn">
              <h3>{t.caregiverVerification}</h3>
              <p>{t.verificationSubtext}</p>
            </div>

            {unreadableRegions.length > 0 && (
              <div className="notice notice-danger">
                <strong>{t.illegibleRegions}</strong>
                <ul>
                  {unreadableRegions.map((r, i) => (
                    <li key={i}>{r.description}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="verify-layout">
              <div className="photo-panel">
                <img src={imagePreview} alt="Prescription document" />
              </div>
              <div>
                {extractedMeds.map((med, idx) => {
                  const isLow = med.confidence < 0.8 || !med.name || !med.strength;
                  return (
                    <div key={idx} className={`med-card ${isLow ? 'low-confidence' : ''}`}>
                      <div className="med-card-top">
                        <span className={`badge ${isLow ? 'badge-warning' : 'badge-ok'}`}>
                          {isLow ? `${t.needsReview} (${(med.confidence * 100).toFixed(0)}%)` : `${t.clearConfidence} (${(med.confidence * 100).toFixed(0)}%)`}
                        </span>
                        <button className="btn btn-danger" onClick={() => handleRemoveMed(idx)}>
                          {t.remove}
                        </button>
                      </div>

                      <label className="field-label" htmlFor={`med-name-${idx}`}>{t.medName}</label>
                      <input
                        id={`med-name-${idx}`}
                        className="input-box"
                        value={med.name || ''}
                        placeholder="e.g. Paracetamol"
                        onChange={(e) => handleMedChange(idx, 'name', e.target.value)}
                      />

                      <div className="two-col">
                        <div>
                          <label className="field-label" htmlFor={`med-strength-${idx}`}>{t.strength}</label>
                          <input
                            id={`med-strength-${idx}`}
                            className="input-box"
                            value={med.strength || ''}
                            placeholder="e.g. 650mg"
                            onChange={(e) => handleMedChange(idx, 'strength', e.target.value)}
                          />
                        </div>
                        <div>
                          <label className="field-label" htmlFor={`med-freq-${idx}`}>{t.frequency}</label>
                          <input
                            id={`med-freq-${idx}`}
                            className="input-box"
                            value={med.frequency_raw || ''}
                            placeholder="e.g. 3 times a day"
                            onChange={(e) => handleMedChange(idx, 'frequency_raw', e.target.value)}
                          />
                        </div>
                      </div>

                      <label className="field-label" htmlFor={`med-instr-${idx}`}>{t.mealDirections}</label>
                      <input
                        id={`med-instr-${idx}`}
                        className="input-box"
                        value={med.instructions || ''}
                        placeholder="e.g. after food"
                        onChange={(e) => handleMedChange(idx, 'instructions', e.target.value)}
                      />

                      <div className="field-label" id={`pill-tag-${idx}`}>{t.pillVisualTag}</div>
                      <div className="chip-row" role="group" aria-labelledby={`pill-tag-${idx}`}>
                        {PILL_TAGS.map((tag) => (
                          <button
                            key={tag}
                            type="button"
                            className={`chip ${med.pill_visual === tag ? 'selected' : ''}`}
                            onClick={() => handleMedChange(idx, 'pill_visual', med.pill_visual === tag ? '' : tag)}
                          >
                            {tag}
                          </button>
                        ))}
                      </div>

                      <div className="source-line">
                        <em>{t.sourceText} "{med.source_text}"</em>
                      </div>
                    </div>
                  );
                })}

                <div className="action-row">
                  <button className="btn btn-secondary" onClick={handleAddMed}>
                    {t.addAnotherMed}
                  </button>
                  <button className="btn btn-primary" onClick={handleConfirmAndProcess}>
                    {t.confirmAndBuild}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 'schedule' && scheduleData && (
          <div className="stack">
            <div className="audio-guide-box">
              <div className="audio-top">
                <h2>{t.dailyAudioExplanation}</h2>
                <button
                  className={`btn btn-speak ${isSpeaking ? 'active' : ''}`}
                  onClick={() => speakText(spokenGuide)}
                >
                  {isSpeaking ? t.stopVoice : t.playAloud}
                </button>
              </div>
              <p>{spokenGuide}</p>
            </div>

            {interactions.length > 0 && (
              <div className="alert-box">
                <h3 className="alert-title">{t.potentialInteraction}</h3>
                {interactions.map((alert, i) => (
                  <div key={i} className="dose-item">
                    <p className="dose-name">
                      {alert.drug_a} + {alert.drug_b} ({alert.severity.toUpperCase()})
                    </p>
                    <p>{alert.description}</p>
                    <p className="dose-instructions">
                      "{alert.message}"
                    </p>
                    <p className="source-line">
                      {t.curatedSource} {alert.source}
                    </p>
                  </div>
                ))}
              </div>
            )}

            <div className="section-head">
              <h2>{t.yourDailyRoutine}</h2>
              <button className="btn-print" onClick={() => window.print()}>
                {t.printSchedule}
              </button>
            </div>

            <div className="print-header">
              <h1>Medicine Safety Assistant — Daily Schedule</h1>
              <p>Printed on: {new Date().toLocaleDateString()}</p>
            </div>

            <div className="schedule-grid">
              <div className="slot-card slot-morning">
                <div className="slot-banner">
                  <span className="slot-title">{t.morning}</span>
                  <span className="slot-meal">{t.breakfast}</span>
                </div>
                <div className="slot-body">
                  {scheduleData.morning.length === 0
                    ? <p className="empty-slot">{t.noMorningMeds}</p>
                    : scheduleData.morning.map(renderDose)}
                </div>
              </div>

              <div className="slot-card slot-afternoon">
                <div className="slot-banner">
                  <span className="slot-title">{t.afternoon}</span>
                  <span className="slot-meal">{t.lunch}</span>
                </div>
                <div className="slot-body">
                  {scheduleData.afternoon.length === 0
                    ? <p className="empty-slot">{t.noAfternoonMeds}</p>
                    : scheduleData.afternoon.map(renderDose)}
                </div>
              </div>

              {scheduleData.evening && scheduleData.evening.length > 0 && (
                <div className="slot-card slot-evening">
                  <div className="slot-banner">
                    <span className="slot-title">{t.evening}</span>
                    <span className="slot-meal">{t.tea}</span>
                  </div>
                  <div className="slot-body">
                    {scheduleData.evening.map(renderDose)}
                  </div>
                </div>
              )}

              <div className="slot-card slot-night">
                <div className="slot-banner">
                  <span className="slot-title">{t.night}</span>
                  <span className="slot-meal">{t.dinnerBedtime}</span>
                </div>
                <div className="slot-body">
                  {scheduleData.night.length === 0
                    ? <p className="empty-slot">{t.noBedtimeMeds}</p>
                    : scheduleData.night.map(renderDose)}
                </div>
              </div>
            </div>

            <div className="panel qa-box">
              <h3>{t.askQuestionTitle}</h3>
              <p className="hint">{t.askQuestionSubtext}</p>
              <div className="qa-row">
                <input
                  className="input-box"
                  aria-label={t.askPlaceholder}
                  placeholder={t.askPlaceholder}
                  value={qaInput}
                  onChange={(e) => setQaInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAskQuestion()}
                />
                <button className="btn btn-primary" onClick={() => handleAskQuestion()}>
                  {t.askBtn}
                </button>
              </div>

              {qaAnswer && (
                <div className="answer-card">
                  <p className="dose-name">{t.assistantReply}</p>
                  <p>{qaAnswer}</p>
                  <button className="btn btn-speak" onClick={() => speakText(qaAnswer)}>
                    {t.readAnswerAloud}
                  </button>
                </div>
              )}
            </div>

            <div className="preview-wrap">
              <button className="btn btn-secondary" onClick={() => setStep('upload')}>
                {t.scanAnother}
              </button>
            </div>
          </div>
        )}
        </main>

        <footer className="footer-disclaimer">
          <strong>{t.footerDisclaimer}</strong>
        </footer>
      </div>
    </div>
  );
}
