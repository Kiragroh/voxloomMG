"""Local, reversible exports with atomic directory publication."""
import json
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from .core import timestamp

def speaker_label(turn, ui_language):
    if not turn.speaker:
        return ""
    if turn.speaker == "?":
        return "Unklar" if ui_language == "de" else "Unclear"
    return ("Person " if ui_language == "de" else "Speaker ") + turn.speaker

def export_all(directory, data, turns, ui_language="de"):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    de = ui_language == "de"
    title = "Transkript" if de else "Transcript"
    note = ("Automatisch erstellt. Bitte Text und Sprecherzuordnung beim Anhören prüfen. * kennzeichnet unsichere Sprecherzuordnungen." if de else "Automatically generated. Please check the text and speaker labels while listening. * marks uncertain speaker assignments.")
    doc = Document()
    doc.core_properties.title = f"VoxLoom · {title}"
    doc.core_properties.author = "VoxLoom"
    section = doc.sections[0]
    section.top_margin = section.bottom_margin = Cm(2)
    section.left_margin = section.right_margin = Cm(2.4)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(8)
    doc.add_heading(title, 0)
    doc.add_paragraph(data["source"])
    p = doc.add_paragraph(note)
    p.runs[0].font.size = Pt(9)
    p.runs[0].font.color.rgb = RGBColor.from_string("657773")
    text_lines = [f"VoxLoom · {title}", data["source"], note, ""]
    subtitle_lines = []
    for index, turn in enumerate(turns, 1):
        label = speaker_label(turn, ui_language)
        mark = " *" if turn.uncertain else ""
        header = f"[{timestamp(turn.start)} – {timestamp(turn.end)}]" + (f"  {label}{mark}" if label else "")
        p = doc.add_paragraph()
        run = p.add_run(header)
        run.bold = True
        run.font.color.rgb = RGBColor.from_string("147C75")
        doc.add_paragraph(turn.text)
        text_lines.extend([header, turn.text, ""])
        subtitle_lines.extend([str(index), f"{timestamp(turn.start, True)} --> {timestamp(max(turn.end, turn.start + 0.1), True)}", (f"{label}: " if label else "") + turn.text, ""])
    section.footer.paragraphs[0].text = "VoxLoom · " + ("Lokal verarbeitet" if de else "Processed locally")
    doc.save(directory / "Transcript.docx")
    (directory / "Transcript.txt").write_text("\n".join(text_lines), encoding="utf-8-sig")
    (directory / "Transcript.srt").write_text("\n".join(subtitle_lines) + "\n", encoding="utf-8")
    (directory / "Transcript.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
