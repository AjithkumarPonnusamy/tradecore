import React, { useState, useRef, useEffect } from "react";
import { 
  X, Mic, Square, Play, Pause, Trash2, RotateCcw, 
  Check, Loader2, AlertCircle, Volume2, Info, CheckSquare, Upload, Save
} from "lucide-react";
import { api } from "@/services/api";

interface VoiceJournalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAutofill: (extractedData: any) => void;
}

type Step = "guide" | "recording" | "review" | "processing" | "results";
type Status = "idle" | "recording" | "paused" | "stopped";

export const VoiceJournalModal: React.FC<VoiceJournalModalProps> = ({ isOpen, onClose, onAutofill }) => {
  const [step, setStep] = useState<Step>("guide");
  const [status, setStatus] = useState<Status>("idle");
  const [timer, setTimer] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progressState, setProgressState] = useState<"recording" | "uploading" | "preparing_audio" | "transcribing" | "analyzing" | "extracting" | "completed">("uploading");
  const [journalId, setJournalId] = useState<string | null>(null);
  const [extractedData, setExtractedData] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Editable Transcript & Parameters
  const [correctedTranscript, setCorrectedTranscript] = useState("");
  const [editedInstrument, setEditedInstrument] = useState("");
  const [editedDirection, setEditedDirection] = useState("");
  const [editedStrategy, setEditedStrategy] = useState("");
  const [editedMarket, setEditedMarket] = useState("");
  const [editedEntryPrice, setEditedEntryPrice] = useState("");
  const [editedStopLoss, setEditedStopLoss] = useState("");
  const [editedTargetPrice, setEditedTargetPrice] = useState("");
  const [editedExitPrice, setEditedExitPrice] = useState("");
  const [editedEntryReason, setEditedEntryReason] = useState("");
  const [editedExitReason, setEditedExitReason] = useState("");
  const [editedTradeManagement, setEditedTradeManagement] = useState("");
  const [editedSummary, setEditedSummary] = useState("");
  const [editedStrengths, setEditedStrengths] = useState("");
  const [editedLessonsLearned, setEditedLessonsLearned] = useState("");
  const [isSavingChanges, setIsSavingChanges] = useState(false);

  useEffect(() => {
    if (extractedData) {
      setCorrectedTranscript(extractedData.corrected_transcript || extractedData.transcript || "");
      const summary = extractedData.ai_summary || {};
      setEditedInstrument(summary.instrument || summary.symbol || "");
      setEditedDirection(summary.direction || "");
      setEditedStrategy(summary.strategy || "");
      setEditedMarket(summary.market || "");
      setEditedEntryPrice(summary.entry_price !== null && summary.entry_price !== undefined ? String(summary.entry_price) : "");
      setEditedStopLoss(summary.stop_loss !== null && summary.stop_loss !== undefined ? String(summary.stop_loss) : "");
      setEditedTargetPrice(summary.target_price !== null && summary.target_price !== undefined ? String(summary.target_price) : summary.target !== null && summary.target !== undefined ? String(summary.target) : "");
      setEditedExitPrice(summary.exit_price !== null && summary.exit_price !== undefined ? String(summary.exit_price) : "");
      setEditedEntryReason(summary.entry_reason || "");
      setEditedExitReason(summary.exit_reason || "");
      setEditedTradeManagement(summary.trade_management || "");
      setEditedSummary(summary.summary || "");
      setEditedStrengths(summary.strengths || "");
      setEditedLessonsLearned(summary.lessons_learned || "");
    }
  }, [extractedData]);

  const handleSaveChanges = async () => {
    if (!journalId) return;
    setIsSavingChanges(true);
    setErrorMessage(null);
    try {
      const updatedSummary = {
        ...extractedData.ai_summary,
        instrument: editedInstrument || null,
        symbol: editedInstrument || null,
        direction: editedDirection || null,
        strategy: editedStrategy || null,
        market: editedMarket || null,
        entry_price: editedEntryPrice ? parseFloat(editedEntryPrice) : null,
        stop_loss: editedStopLoss ? parseFloat(editedStopLoss) : null,
        target_price: editedTargetPrice ? parseFloat(editedTargetPrice) : null,
        target: editedTargetPrice ? parseFloat(editedTargetPrice) : null,
        exit_price: editedExitPrice ? parseFloat(editedExitPrice) : null,
        entry_reason: editedEntryReason || null,
        exit_reason: editedExitReason || null,
        trade_management: editedTradeManagement || null,
        summary: editedSummary || "",
        strengths: editedStrengths || null,
        lessons_learned: editedLessonsLearned || null
      };

      const payload = {
        corrected_transcript: correctedTranscript,
        ai_summary: updatedSummary
      };

      const res = await api.voiceJournal.update(journalId, payload);
      setExtractedData(res);
      alert("Changes saved to database successfully.");
    } catch (err: any) {
      console.error("Save error:", err);
      setErrorMessage(err.message || "Failed to save updated voice journal.");
    } finally {
      setIsSavingChanges(false);
    }
  };
  
  // MediaRecorder references
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);


  // Waveform Visualizer
  const startVisualizer = (stream: MediaStream) => {
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioContextClass();
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 128;
      
      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      audioContextRef.current = audioCtx;
      analyserRef.current = analyser;

      drawVisualizer();
    } catch (e) {
      console.error("Error setting up audio visualizer:", e);
    }
  };

  const stopVisualizer = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(e => console.error(e));
    }
    audioContextRef.current = null;
    analyserRef.current = null;
  };

  const drawVisualizer = () => {
    if (!canvasRef.current || !analyserRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      if (!analyserRef.current) return;
      animationFrameRef.current = requestAnimationFrame(draw);

      analyser.getByteFrequencyData(dataArray);

      ctx.fillStyle = "#111420"; // Match panel bg
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.0;
      let barHeight;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        barHeight = dataArray[i] / 1.5;

        // Custom HSL gradients matching tv-blue
        ctx.fillStyle = `hsla(217, 91%, ${Math.min(40 + barHeight / 2, 75)}%, 0.95)`;
        
        // Draw double mirrored visualizer
        ctx.fillRect(x, canvas.height / 2 - barHeight / 2, barWidth - 2, barHeight);
        x += barWidth;
      }
    };

    draw();
  };

  // Timer logic
  const startTimer = () => {
    stopTimer();
    timerRef.current = setInterval(() => {
      setTimer(prev => prev + 1);
    }, 1000);
  };

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, "0");
    const s = (secs % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  // MediaRecorder operations
  const startRecording = async () => {
    setErrorMessage(null);
    audioChunksRef.current = [];
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const audioUrl = URL.createObjectURL(audioBlob);
        setAudioBlob(audioBlob);
        setAudioUrl(audioUrl);
        setStep("review");
      };

      mediaRecorder.start();
      setStatus("recording");
      setTimer(0);
      startTimer();
      startVisualizer(stream);
      setStep("recording");
    } catch (e: any) {
      console.error(e);
      setErrorMessage("Could not access microphone. Please enable microphone permissions in your browser.");
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && status === "recording") {
      mediaRecorderRef.current.pause();
      setStatus("paused");
      stopTimer();
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && status === "paused") {
      mediaRecorderRef.current.resume();
      setStatus("recording");
      startTimer();
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && (status === "recording" || status === "paused")) {
      mediaRecorderRef.current.stop();
      setStatus("stopped");
      stopTimer();
      stopVisualizer();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
    }
  };

  const resetRecording = () => {
    stopTimer();
    stopVisualizer();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
    }
    setAudioUrl(null);
    setAudioBlob(null);
    setTimer(0);
    setStatus("idle");
    setStep("guide");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const file = files[0];
    
    // Validate format
    const allowedExtensions = [".mp3", ".wav", ".m4a", ".webm", ".ogg"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    
    if (!allowedExtensions.includes(ext)) {
      setErrorMessage("Unsupported audio file format. Please upload mp3, wav, m4a, or webm.");
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    setErrorMessage(null);
    setAudioBlob(file);
    const url = URL.createObjectURL(file);
    setAudioUrl(url);
    setStatus("stopped");
    setStep("review");
  };

  // Audio Playback
  const togglePlayAudio = () => {
    if (!audioUrl) return;
    
    if (audioPlayerRef.current) {
      if (isPlaying) {
        audioPlayerRef.current.pause();
        setIsPlaying(false);
      } else {
        audioPlayerRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  // Background Whisper + GPT Extraction
  const processRecording = async () => {
    if (!audioBlob) return;
    
    setStep("processing");
    setProgressState("uploading");
    setErrorMessage(null);

    try {
      // 1. Upload audio
      const response = await api.voiceJournal.upload(audioBlob);
      const journalId = response.id;
      setJournalId(journalId);
      
      setProgressState("transcribing");

      // 2. Poll status
      pollJournalStatus(journalId);
    } catch (err: any) {
      console.error("Upload error:", err);
      setErrorMessage(err.message || "Failed to upload audio recording to backend.");
      setStep("review");
    }
  };

  const pollJournalStatus = (id: string) => {
    let attempts = 0;
    const maxAttempts = 120; // 3 minutes max (since large-v3 takes longer first load)
    
    const interval = setInterval(async () => {
      attempts++;
      if (attempts > maxAttempts) {
        clearInterval(interval);
        setErrorMessage("AI processing timed out. Please check logs.");
        setStep("review");
        return;
      }

      try {
        const journal = await api.voiceJournal.getStatus(id);
        
        if (journal.status === "PREPARING_AUDIO") {
          setProgressState("preparing_audio");
        } else if (journal.status === "TRANSCRIBING") {
          setProgressState("transcribing");
        } else if (journal.status === "ANALYZING") {
          setProgressState("analyzing");
        } else if (journal.status === "EXTRACTING") {
          setProgressState("extracting");
        } else if (journal.status === "COMPLETED") {
          clearInterval(interval);
          setExtractedData(journal);
          setProgressState("completed");
          setStep("results");
        } else if (journal.status === "FAILED") {
          clearInterval(interval);
          setErrorMessage(journal.error_message || "AI Analysis failed on server.");
          setStep("review");
        }
      } catch (err: any) {
        console.error("Polling error:", err);
        if (attempts > 30) {
          clearInterval(interval);
          setErrorMessage("Failed to retrieve processing status.");
          setStep("review");
        }
      }
    }, 1500);
  };

  // Perform autofill patch and close
  const handleAutofillConfirm = () => {
    if (extractedData) {
      onAutofill(extractedData);
      onClose();
      resetRecording();
    }
  };

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopTimer();
      stopVisualizer();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
    };
  }, []);


  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-tv-bg/80 backdrop-blur-md fade-in">
      <div className="w-full max-w-2xl bg-tv-panel border border-tv-border rounded-2xl overflow-hidden shadow-2xl slide-up flex flex-col max-h-[85vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-tv-border">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-tv-blue/10 rounded-lg">
              <Mic className="w-5 h-5 text-tv-blue animate-pulse-halo" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-tv-text-highlight">AI Voice Trade Journal</h2>
              <p className="text-xs text-tv-muted">Describe your trade. AI will extract parameters and auto-fill notes.</p>
            </div>
          </div>
          <button 
            onClick={() => { onClose(); resetRecording(); }}
            className="text-tv-muted hover:text-tv-text-highlight transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Errors Alert */}
        {errorMessage && (
          <div className="mx-5 mt-4 p-3.5 bg-tv-red/10 border border-tv-red/20 rounded-xl flex gap-2.5 text-xs text-tv-red items-start">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold">Error:</span> {errorMessage}
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* STEP 1: GUIDE / INSTRUCTIONS */}
          {step === "guide" && (
            <div className="space-y-4">
              <div className="p-4 bg-tv-blue/5 border border-tv-blue/10 rounded-xl space-y-2">
                <h3 className="text-sm font-semibold text-tv-blue flex items-center gap-1.5">
                  <Info className="w-4 h-4" />
                  Recording Template Guide
                </h3>
                <p className="text-xs text-tv-muted leading-relaxed">
                  Please describe your trade in the following order for optimal AI extraction accuracy:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 pl-1.5 text-xs text-tv-muted font-medium">
                  <div>1. Instrument Traded (e.g. XAUUSD, NIFTY)</div>
                  <div>2. Direction (Buy or Sell)</div>
                  <div>3. Setup / Strategy configuration</div>
                  <div>4. Entry price details</div>
                  <div>5. Stop loss location</div>
                  <div>6. Profit targets</div>
                  <div>7. Management / Exit reasons</div>
                  <div>8. Emotions felt during the trade</div>
                  <div>9. Mistakes made & lessons learned</div>
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-xs font-semibold text-tv-text-highlight">Speak Naturally & Include:</span>
                <div className="grid grid-cols-2 gap-2 text-xs text-tv-muted">
                  {[
                    "Symbol/Instrument", "Direction (BUY/SELL)", "Entry price",
                    "Stop Loss & Target", "Strategy Setup", "Exit Reason",
                    "Mindset & Emotions", "Mistakes & Lessons"
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <Check className="w-3.5 h-3.5 text-tv-green shrink-0" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex flex-col items-center justify-center pt-6 gap-4">
                <div className="flex flex-wrap items-center justify-center gap-3 w-full">
                  <button
                    onClick={startRecording}
                    className="flex items-center gap-2 bg-tv-blue hover:bg-tv-blue-hover text-white px-6 py-3 rounded-full text-sm font-bold shadow-lg shadow-tv-blue/20 hover:shadow-tv-blue/35 transition-all cursor-pointer transform hover:-translate-y-0.5"
                  >
                    <Mic className="w-4 h-4" />
                    Start Recording Note
                  </button>
                  
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-2 bg-tv-bg hover:bg-tv-hover border border-tv-border text-tv-text-highlight px-6 py-3 rounded-full text-sm font-bold shadow-md hover:shadow-lg transition-all cursor-pointer transform hover:-translate-y-0.5"
                  >
                    <Upload className="w-4 h-4" />
                    Upload Audio File
                  </button>
                </div>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileUpload}
                  accept="audio/mp3,audio/wav,audio/m4a,audio/webm,audio/mpeg,audio/ogg"
                  className="hidden"
                />
                <span className="text-[10px] text-tv-muted">Supported formats: mp3, wav, m4a, webm (max 25MB)</span>
              </div>
            </div>
          )}

          {/* STEP 2: RECORDING PANEL */}
          {step === "recording" && (
            <div className="space-y-6">
              
              {/* Template Guide (shown while recording) */}
              <div className="p-4 bg-tv-blue/5 border border-tv-blue/10 rounded-xl space-y-2">
                <h3 className="text-sm font-semibold text-tv-blue flex items-center gap-1.5">
                  <Info className="w-4 h-4" />
                  Recording Template Guide
                </h3>
                <p className="text-xs text-tv-muted leading-relaxed">
                  Please describe your trade in the following order for optimal AI extraction accuracy:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2 pl-1.5 text-xs text-tv-muted font-medium">
                  <div>1. Instrument Traded (e.g. XAUUSD, NIFTY)</div>
                  <div>2. Direction (Buy or Sell)</div>
                  <div>3. Setup / Strategy configuration</div>
                  <div>4. Entry price details</div>
                  <div>5. Stop loss location</div>
                  <div>6. Profit targets</div>
                  <div>7. Management / Exit reasons</div>
                  <div>8. Emotions felt during the trade</div>
                  <div>9. Mistakes made & lessons learned</div>
                </div>
              </div>

              {/* Speak Naturally Checklist (shown while recording) */}
              <div className="space-y-2 pb-2 border-b border-tv-border/20">
                <span className="text-xs font-semibold text-tv-text-highlight">Speak Naturally & Include:</span>
                <div className="grid grid-cols-2 gap-2 text-xs text-tv-muted">
                  {[
                    "Symbol/Instrument", "Direction (BUY/SELL)", "Entry price",
                    "Stop Loss & Target", "Strategy Setup", "Exit Reason",
                    "Mindset & Emotions", "Mistakes & Lessons"
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <Check className="w-3.5 h-3.5 text-tv-green shrink-0" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Status and Audio elements */}
              <div className="flex flex-col items-center justify-center space-y-5 pt-2">
                <div className="text-center">
                  <span className="text-3xl font-extrabold text-tv-text-highlight font-mono tracking-wider">
                    {formatTime(timer)}
                  </span>
                  <p className="text-xs text-tv-muted mt-1 uppercase tracking-widest font-semibold flex items-center justify-center gap-1.5">
                    <span className={`w-2.5 h-2.5 rounded-full ${status === "recording" ? "bg-tv-red animate-pulse" : "bg-yellow-500"}`} />
                    {status === "recording" ? "Recording Live Note..." : "Recording Paused"}
                  </p>
                </div>

                {/* Real Audio Waveform Canvas */}
                <div className="w-full h-24 border border-tv-border/20 rounded-xl overflow-hidden shadow-inner bg-[#111420]">
                  <canvas ref={canvasRef} className="w-full h-full" width={600} height={96} />
                </div>

                {/* Controls */}
                <div className="flex items-center gap-4">
                  {status === "recording" ? (
                    <button
                      onClick={pauseRecording}
                      className="flex items-center justify-center w-12 h-12 bg-tv-bg hover:bg-tv-hover border border-tv-border text-tv-text-highlight rounded-full transition-colors cursor-pointer"
                      title="Pause Recording"
                    >
                      <Pause className="w-5 h-5" />
                    </button>
                  ) : (
                    <button
                      onClick={resumeRecording}
                      className="flex items-center justify-center w-12 h-12 bg-tv-blue/10 hover:bg-tv-blue/20 text-tv-blue rounded-full transition-colors cursor-pointer"
                      title="Resume Recording"
                    >
                      <Play className="w-5 h-5" />
                    </button>
                  )}

                  <button
                    onClick={stopRecording}
                    className="flex items-center justify-center w-16 h-16 bg-tv-red hover:bg-tv-red-hover text-white rounded-full transition-all cursor-pointer shadow-lg shadow-tv-red/20 transform hover:scale-105"
                    title="Stop and Review"
                  >
                    <Square className="w-6 h-6 fill-white" />
                  </button>

                  <button
                    onClick={resetRecording}
                    className="flex items-center justify-center w-12 h-12 bg-tv-bg hover:bg-tv-hover border border-tv-border text-tv-muted hover:text-tv-text-highlight rounded-full transition-colors cursor-pointer"
                    title="Cancel & Reset"
                  >
                    <RotateCcw className="w-5 h-5" />
                  </button>
                </div>
              </div>

            </div>
          )}

          {/* STEP 3: REVIEW / PLAYBACK */}
          {step === "review" && (
            <div className="space-y-6">
              <div className="p-5 bg-tv-panel border border-tv-border rounded-xl space-y-4">
                <span className="text-xs font-bold text-tv-muted uppercase tracking-wider block">Review Recorded Audio</span>
                
                {/* Visual Audio Bar */}
                <div className="flex items-center gap-3 bg-tv-bg border border-tv-border/20 rounded-xl p-3">
                  <button
                    onClick={togglePlayAudio}
                    className="p-2.5 bg-tv-blue hover:bg-tv-blue-hover text-white rounded-lg transition-colors cursor-pointer shrink-0"
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-white" />}
                  </button>
                  <div className="flex-1 h-1.5 bg-tv-border/30 rounded-full overflow-hidden relative">
                    <div className={`h-full bg-tv-blue ${isPlaying ? "w-full transition-all duration-[30s] ease-linear" : "w-0"}`} />
                  </div>
                  <span className="text-xs font-mono text-tv-muted font-bold tracking-tight">
                    {formatTime(timer)}
                  </span>
                </div>

                <audio 
                  ref={audioPlayerRef} 
                  src={audioUrl || ""} 
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onEnded={() => setIsPlaying(false)}
                  onLoadedMetadata={(e) => setTimer(Math.round(e.currentTarget.duration))}
                  className="hidden" 
                />

                <div className="flex items-center gap-3">
                  <button
                    onClick={processRecording}
                    className="flex-1 flex items-center justify-center gap-2 bg-tv-green hover:bg-tv-green-hover text-white py-3 rounded-xl text-sm font-bold shadow-lg shadow-tv-green/10 transition-colors cursor-pointer"
                  >
                    <Check className="w-4 h-4" />
                    Transcribe & Extract with AI
                  </button>
                  
                  <button
                    onClick={resetRecording}
                    className="p-3 bg-tv-bg hover:bg-tv-hover border border-tv-border text-tv-muted hover:text-tv-text-highlight rounded-xl transition-colors cursor-pointer"
                    title="Delete and Re-record"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 4: PROCESSING STATUS */}
          {step === "processing" && (
            <div className="flex flex-col items-center justify-center py-10 space-y-6">
              <Loader2 className="w-12 h-12 text-tv-blue animate-spin" />
              <div className="text-center space-y-1">
                <h3 className="text-base font-bold text-tv-text-highlight capitalize">
                  {progressState === "uploading" && "Uploading audio file..."}
                  {progressState === "preparing_audio" && "Preparing Audio (Noise Reduction)..."}
                  {progressState === "transcribing" && "Transcribing voice to text..."}
                  {progressState === "analyzing" && "Analyzing Vocabulary..."}
                  {progressState === "extracting" && "Extracting Trade Information..."}
                  {progressState === "completed" && "Analysis Completed!"}
                </h3>
                <p className="text-xs text-tv-muted max-w-sm">
                  {progressState === "uploading" && "Transmitting your voice journal to secure backend storage."}
                  {progressState === "preparing_audio" && "Running noise-gate, high/low-pass filters and VAD."}
                  {progressState === "transcribing" && "Running Faster-Whisper speech recognition."}
                  {progressState === "analyzing" && "Correcting trading abbreviations and terminology."}
                  {progressState === "extracting" && "Extracting structured trade parameters and lessons."}
                  {progressState === "completed" && "Rendering extraction parameters form."}
                </p>
              </div>

              {/* Progress Tracker */}
              <div className="w-full max-w-md space-y-2">
                <div className="h-1 bg-tv-border/20 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-tv-blue transition-all duration-500 ease-out" 
                    style={{
                      width: progressState === "uploading" ? "15%" : 
                             progressState === "preparing_audio" ? "35%" :
                             progressState === "transcribing" ? "55%" : 
                             progressState === "analyzing" ? "75%" : 
                             progressState === "extracting" ? "90%" : "100%"
                    }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-tv-muted font-bold uppercase tracking-wider gap-1.5 flex-wrap">
                  <span className={progressState === "uploading" ? "text-tv-blue" : ""}>Upload</span>
                  <span className={progressState === "preparing_audio" ? "text-tv-blue" : ""}>Prep</span>
                  <span className={progressState === "transcribing" ? "text-tv-blue" : ""}>Transcribe</span>
                  <span className={progressState === "analyzing" ? "text-tv-blue" : ""}>Analyze</span>
                  <span className={progressState === "extracting" ? "text-tv-blue" : ""}>Extract</span>
                </div>
              </div>
            </div>
          )}

          {/* STEP 5: EXTRACTION RESULTS PREVIEW */}
          {step === "results" && extractedData && (
            <div className="space-y-5 slide-up">
              {/* Warnings/Success message */}
              {extractedData.error_message && (
                <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 text-yellow-600 rounded-xl text-xs flex gap-2">
                  <Info className="w-4 h-4 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Message:</span> {extractedData.error_message}
                  </div>
                </div>
              )}

              {/* Original Transcript */}
              <div className="space-y-1.5">
                <span className="text-xs font-bold text-tv-muted uppercase tracking-wider">Original Transcript</span>
                <div className="p-4 bg-tv-bg border border-tv-border/30 rounded-xl text-xs text-tv-text-highlight leading-relaxed italic opacity-85 select-none">
                  "{extractedData.original_transcript || extractedData.transcript}"
                </div>
              </div>

              {/* Corrected Transcript */}
              <div className="space-y-1.5">
                <span className="text-xs font-bold text-tv-muted uppercase tracking-wider">Corrected Transcript (Edit if needed)</span>
                <textarea
                  value={correctedTranscript}
                  onChange={(e) => setCorrectedTranscript(e.target.value)}
                  rows={4}
                  className="w-full bg-tv-bg border border-tv-border/30 rounded-xl p-4 text-xs text-tv-text-highlight leading-relaxed focus:border-tv-blue focus:ring-1 focus:ring-tv-blue/30 focus:outline-none transition-all"
                />
              </div>

              {/* Extracted Structured Parameters */}
              <div className="space-y-3">
                <span className="text-xs font-bold text-tv-muted uppercase tracking-wider">AI Extracted Parameters</span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                  <div>
                    <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">Instrument</label>
                    <input
                      type="text"
                      value={editedInstrument}
                      onChange={(e) => setEditedInstrument(e.target.value)}
                      className="w-full bg-tv-bg border border-tv-border/30 rounded-lg px-3 py-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">Direction</label>
                    <select
                      value={editedDirection}
                      onChange={(e) => setEditedDirection(e.target.value)}
                      className="w-full bg-tv-bg border border-tv-border/30 rounded-lg px-3 py-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30 cursor-pointer"
                    >
                      <option value="">Select Direction</option>
                      <option value="BUY">BUY</option>
                      <option value="SELL">SELL</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">Strategy</label>
                    <input
                      type="text"
                      value={editedStrategy}
                      onChange={(e) => setEditedStrategy(e.target.value)}
                      className="w-full bg-tv-bg border border-tv-border/30 rounded-lg px-3 py-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">Market Segment</label>
                    <input
                      type="text"
                      value={editedMarket}
                      onChange={(e) => setEditedMarket(e.target.value)}
                      className="w-full bg-tv-bg border border-tv-border/30 rounded-lg px-3 py-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">Entry Price</label>
                    <input
                      type="text"
                      value={editedEntryPrice}
                      onChange={(e) => setEditedEntryPrice(e.target.value)}
                      className="w-full bg-tv-bg border border-tv-border/30 rounded-lg px-3 py-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">Stop Loss</label>
                    <input
                      type="text"
                      value={editedStopLoss}
                      onChange={(e) => setEditedStopLoss(e.target.value)}
                      className="w-full bg-tv-bg border border-tv-border/30 rounded-lg px-3 py-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">Target Price</label>
                    <input
                      type="text"
                      value={editedTargetPrice}
                      onChange={(e) => setEditedTargetPrice(e.target.value)}
                      className="w-full bg-tv-bg border border-tv-border/30 rounded-lg px-3 py-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">Exit Price</label>
                    <input
                      type="text"
                      value={editedExitPrice}
                      onChange={(e) => setEditedExitPrice(e.target.value)}
                      className="w-full bg-tv-bg border border-tv-border/30 rounded-lg px-3 py-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">Entry Reason</label>
                    <input
                      type="text"
                      value={editedEntryReason}
                      onChange={(e) => setEditedEntryReason(e.target.value)}
                      className="w-full bg-tv-bg border border-tv-border/30 rounded-lg px-3 py-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">Exit Reason</label>
                    <input
                      type="text"
                      value={editedExitReason}
                      onChange={(e) => setEditedExitReason(e.target.value)}
                      className="w-full bg-tv-bg border border-tv-border/30 rounded-lg px-3 py-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">Trade Management</label>
                    <input
                      type="text"
                      value={editedTradeManagement}
                      onChange={(e) => setEditedTradeManagement(e.target.value)}
                      className="w-full bg-tv-bg border border-tv-border/30 rounded-lg px-3 py-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                    />
                  </div>
                </div>
              </div>

              {/* Emotion tags */}
              {extractedData.emotion_tags && extractedData.emotion_tags.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-xs font-bold text-tv-muted uppercase tracking-wider">Detected Emotions</span>
                  <div className="flex flex-wrap gap-2">
                    {extractedData.emotion_tags.map((emo: any, idx: number) => (
                      <span 
                        key={idx} 
                        className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg bg-tv-blue/10 border border-tv-blue/20 text-tv-blue shadow-sm"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                        {emo.tag} ({(emo.confidence * 100).toFixed(0)}% confidence)
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Summary / Mindset Textareas */}
              <div className="p-4 bg-tv-blue/5 border border-tv-blue/15 rounded-xl space-y-3.5">
                <div>
                  <label className="block text-[10px] font-bold text-tv-muted uppercase tracking-wider mb-1.5">AI Trade Summary</label>
                  <textarea
                    value={editedSummary}
                    onChange={(e) => setEditedSummary(e.target.value)}
                    rows={2}
                    className="w-full bg-tv-bg border border-tv-border/30 rounded-lg p-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-tv-green uppercase tracking-wider mb-1.5">Key Strengths</label>
                  <textarea
                    value={editedStrengths}
                    onChange={(e) => setEditedStrengths(e.target.value)}
                    rows={2}
                    className="w-full bg-tv-bg border border-tv-border/30 rounded-lg p-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-tv-blue uppercase tracking-wider mb-1.5">Lessons Learned</label>
                  <textarea
                    value={editedLessonsLearned}
                    onChange={(e) => setEditedLessonsLearned(e.target.value)}
                    rows={2}
                    className="w-full bg-tv-bg border border-tv-border/30 rounded-lg p-2 text-xs text-tv-text-highlight focus:border-tv-blue focus:outline-none focus:ring-1 focus:ring-tv-blue/30"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-3 pt-2">
                <button
                  onClick={handleSaveChanges}
                  disabled={isSavingChanges}
                  className="flex-1 min-w-[120px] flex items-center justify-center gap-2 bg-tv-blue hover:bg-tv-blue-hover text-white py-3.5 rounded-xl text-sm font-bold shadow-lg shadow-tv-blue/10 transition-colors cursor-pointer disabled:opacity-50 select-none"
                >
                  {isSavingChanges ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4" />
                      Save Changes
                    </>
                  )}
                </button>
                <button
                  onClick={handleAutofillConfirm}
                  className="flex-[2] min-w-[200px] flex items-center justify-center gap-2 bg-tv-green hover:bg-tv-green-hover text-white py-3.5 rounded-xl text-sm font-bold shadow-lg shadow-tv-green/10 transition-colors cursor-pointer select-none"
                >
                  <CheckSquare className="w-4 h-4" />
                  Confirm & Auto-fill Fields
                </button>
                <button
                  onClick={resetRecording}
                  className="px-4 py-3.5 bg-tv-bg hover:bg-tv-hover border border-tv-border text-tv-muted hover:text-tv-text-highlight rounded-xl text-sm font-semibold transition-colors cursor-pointer select-none"
                >
                  Discard
                </button>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
};
