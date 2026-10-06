"""Offline worker. No account, downloader or cloud backend at runtime."""
import os
import sys

# Set these before importing any library that can resolve Hub resources.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["DO_NOT_TRACK"] = "1"

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from .core import align, document_data, safe_stem
from .export import export_all

def emit(kind, **fields):
    print(json.dumps({"event": kind, **fields}, ensure_ascii=True), flush=True)

def check_models(root, speakers=True):
    root = Path(root)
    required = ["whisper-small/model.bin", "whisper-small/config.json", "whisper-small/tokenizer.json"]
    if speakers:
        required += ["speakers/model.int8.onnx", "speakers/embedding.onnx"]
    missing = [name for name in required if not (root / name).is_file() or (root / name).stat().st_size == 0]
    if not any((root / "whisper-small" / name).is_file() for name in ("vocabulary.json", "vocabulary.txt")):
        missing.append("vocabulary")
    if missing:
        raise FileNotFoundError("models_missing")

class Engine:
    def __init__(self, models):
        self.models = Path(models)
        self.whisper = None
        self.diarizer = None
        self.speaker_count = None

    def load(self):
        if self.whisper is None:
            from faster_whisper import WhisperModel
            self.whisper = WhisperModel(str(self.models / "whisper-small"), device="cpu", compute_type="int8", cpu_threads=max(1, min(8, (os.cpu_count() or 2) - 1)), num_workers=1, local_files_only=True)

    def speakers(self, samples, count, callback):
        import sherpa_onnx as so
        if self.diarizer is None or self.speaker_count != count:
            threads = max(1, min(4, (os.cpu_count() or 2) - 1))
            config = so.OfflineSpeakerDiarizationConfig(
                segmentation=so.OfflineSpeakerSegmentationModelConfig(pyannote=so.OfflineSpeakerSegmentationPyannoteModelConfig(model=str(self.models / "speakers" / "model.int8.onnx")), num_threads=threads, provider="cpu"),
                embedding=so.SpeakerEmbeddingExtractorConfig(model=str(self.models / "speakers" / "embedding.onnx"), num_threads=threads, provider="cpu"),
                clustering=so.FastClusteringConfig(num_clusters=count if count > 0 else -1, threshold=0.5),
                min_duration_on=0.3, min_duration_off=0.5,
            )
            if not config.validate():
                raise RuntimeError("speaker_models_invalid")
            self.diarizer = so.OfflineSpeakerDiarization(config)
            self.speaker_count = count
        spans = self.diarizer.process(samples, callback=lambda done, total: callback(done / max(1, total))).sort_by_start_time()
        return [(s.start, s.end, s.speaker) for s in spans]

    def transcribe(self, path, options, progress):
        from faster_whisper.audio import decode_audio
        progress(0, "reading")
        samples = decode_audio(str(path), sampling_rate=16000)
        duration = len(samples) / 16000
        if duration < 0.2:
            raise ValueError("audio_empty")
        progress(2, "loading")
        self.load()
        progress(5, "transcribing")
        segments, info = self.whisper.transcribe(samples, language=options.get("language") or None, beam_size=5, word_timestamps=True, vad_filter=True, vad_parameters={"min_silence_duration_ms": 500}, condition_on_previous_text=False)
        words = []
        with_speakers = options.get("speakers", True)
        ceiling = 65 if with_speakers else 94
        for segment in segments:
            if segment.words:
                words.extend((word.start, word.end, word.word) for word in segment.words)
            elif segment.text.strip():
                words.append((segment.start, segment.end, segment.text))
            progress(min(ceiling, 5 + (ceiling - 5) * segment.end / duration), "transcribing")
        if not words:
            raise ValueError("no_speech")
        spans = None
        if with_speakers:
            progress(65, "speakers")
            spans = self.speakers(samples, options.get("speaker_count", -1), lambda portion: (progress(65 + 29 * portion, "speakers"), 0)[1])
        turns = align(words, spans)
        return document_data(path, turns, info.language, duration, with_speakers), turns

def error_code(exc):
    known = {"models_missing", "speaker_models_invalid", "audio_empty", "no_speech"}
    if str(exc) in known:
        return str(exc)
    if isinstance(exc, PermissionError):
        return "permission"
    if isinstance(exc, MemoryError) or "memory" in str(exc).lower():
        return "memory"
    return "processing_failed"

def run_job(job):
    engine = Engine(job["models"])
    check_models(job["models"], job["options"].get("speakers", True))
    output = Path(job["output"])
    output.mkdir(parents=True, exist_ok=True)
    for index, source in enumerate(job["files"]):
        staging = output / (".voxloom-" + job["id"] + "-" + str(index))
        try:
            emit("started", index=index)
            data, turns = engine.transcribe(source, job["options"], lambda percent, stage: emit("progress", index=index, percent=round(percent), stage=stage))
            emit("progress", index=index, percent=96, stage="exporting")
            export_all(staging, data, turns, job["options"].get("ui_language", "de"))
            destination = output / (safe_stem(source) + "_" + datetime.now().strftime("%Y%m%d-%H%M%S") + "_" + uuid.uuid4().hex[:6])
            staging.rename(destination)
            emit("completed", index=index, directory=str(destination), turns=len(turns), duration=data["duration_seconds"])
        except Exception as exc:
            if staging.exists():
                shutil.rmtree(staging)
            # Do not put interview contents or tracebacks into persistent application logs.
            emit("failed", index=index, code=error_code(exc))
    emit("finished")

def worker(job_path):
    try:
        run_job(json.loads(Path(job_path).read_text(encoding="utf-8")))
    except Exception as exc:
        emit("fatal", code=error_code(exc))
        return 1
    return 0
