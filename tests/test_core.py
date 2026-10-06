import json
from pathlib import Path
from docx import Document
from voxloom.core import Turn, align, document_data, safe_stem, speaker_for, timestamp
from voxloom.export import export_all

def test_alignment_splits_inside_whisper_segment():
    words = [(0, 0.8, " Guten"), (0.8, 1.4, " Tag."), (1.6, 2.1, " Hallo."), (2.2, 2.8, " Danke.")]
    turns = align(words, [(0, 1.5, 7), (1.5, 3.0, 3)])
    assert [(t.speaker, t.text) for t in turns] == [("1", "Guten Tag."), ("2", "Hallo. Danke.")]

def test_unknown_and_overlap_do_not_invent_speakers():
    assert speaker_for(3, 4, [(0, 1, 0)]) == ("?", True)
    speaker, unclear = speaker_for(0, 1, [(0, 1, 0), (0, 0.8, 1)])
    assert speaker == "0" and unclear

def test_long_monologue_and_silence_split_paragraphs():
    turns = align([(0, 1, "Hello."), (4, 5, "Hello."), (5, 70, "Again.")])
    assert len(turns) == 3
    assert turns[0].text == turns[1].text  # Intentional repetitions must survive.

def test_hour_timestamps_and_reserved_filenames():
    assert timestamp(3661.123, True) == "01:01:01,123"
    assert safe_stem("CON.mp3") == "Recording"
    assert safe_stem("a?b.mp3") == "a_b"

def test_exports_preserve_unicode_speakers_and_uncertainty(tmp_path):
    turns = [Turn(0.25, 3.8, "Ärzte hören zu.", "1"), Turn(4, 7, "Thank you.", "?", True)]
    data = document_data("Interview.mp3", turns, "de", 8, True)
    export_all(tmp_path, data, turns, "en")
    doc = Document(tmp_path / "Transcript.docx")
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Speaker 1" in text and "Ärzte hören zu." in text and "Unclear *" in text
    assert json.loads((tmp_path / "Transcript.json").read_text(encoding="utf-8")) == data
    assert "00:00:00,250 --> 00:00:03,800" in (tmp_path / "Transcript.srt").read_text()

def test_german_export(tmp_path):
    turns = [Turn(0, 1, "Hallo", "1")]
    export_all(tmp_path, document_data("a.wav", turns, "de", 1, True), turns, "de")
    assert "Person 1" in (tmp_path / "Transcript.txt").read_text(encoding="utf-8-sig")
