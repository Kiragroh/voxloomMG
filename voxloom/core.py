"""Transcript representation and word-level alignment, independent of ML libraries."""
from dataclasses import asdict, dataclass
from pathlib import Path
import re

SUPPORTED = {".wav", ".mp3", ".m4a", ".mp4", ".flac", ".ogg", ".aac", ".wma", ".opus", ".aiff", ".aif"}

@dataclass
class Turn:
    start: float
    end: float
    text: str
    speaker: str = ""
    uncertain: bool = False

def timestamp(seconds, milliseconds=False):
    total = max(0, round(seconds * 1000))
    hours, rest = divmod(total, 3600000)
    minutes, rest = divmod(rest, 60000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}" + (f",{ms:03}" if milliseconds else "")

def speaker_for(start, end, spans):
    scores = {}
    for span in spans:
        overlap = max(0.0, min(end, span[1]) - max(start, span[0]))
        if overlap:
            scores[span[2]] = scores.get(span[2], 0.0) + overlap
    if not scores:
        return "?", True
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ambiguous = len(ordered) > 1 and ordered[1][1] > ordered[0][1] * 0.6
    return str(ordered[0][0]), ambiguous

def align(words, spans=None):
    result = []
    labels = {}
    for start, end, text in words:
        if not text.strip():
            continue
        speaker, uncertain = speaker_for(start, end, spans) if spans is not None else ("", False)
        if speaker not in ("?", ""):
            labels.setdefault(speaker, str(len(labels) + 1))
            speaker = labels[speaker]
        # Keep paragraphs comfortably short for correction, even for long monologues.
        if result and result[-1].speaker == speaker and start - result[-1].end < 2.0 and end - result[-1].start < 60.0:
            previous = result[-1]
            previous.text += text if text[:1].isspace() or text[:1] in ",.!?:;" else " " + text
            previous.end = end
            previous.uncertain |= uncertain
        else:
            result.append(Turn(start, end, text.strip(), speaker, uncertain))
    return result

def safe_stem(path):
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", Path(path).stem).strip(" .")[:100]
    if not stem or stem.upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        stem = "Recording"
    return stem

def document_data(source, turns, language, duration, diarization):
    return {"schema": 1, "app": "VoxLoom", "source": Path(source).name, "language": language, "duration_seconds": duration, "speaker_detection": diarization, "turns": [asdict(turn) for turn in turns]}
