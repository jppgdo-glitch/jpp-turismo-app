from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from scripts.create_jppturismo_ordem import COMPANY, clean


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "pdf" / "orcamentos"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def value(data: dict, key: str, default: str = "") -> str:
    return clean(data.get(key), default)


def first_name(name: str) -> str:
    name = clean(name).title()
    for prefix in ["Seu ", "Sra ", "Sr ", "Senhora ", "Senhor "]:
        if name.startswith(prefix):
            return name
    return name or "Cliente"


def passenger_summary(data: dict) -> str:
    parts = []
    labels = [("adt", "adulto"), ("chd", "crianca"), ("inf", "infantil"), ("sen", "senior"), ("free", "free")]
    total = 0
    for key, label in labels:
        try:
            count = int(value(data, key, "0") or "0")
        except ValueError:
            count = 0
        total += count
        if count:
            suffix = "s" if count > 1 and label != "free" else ""
            parts.append(f"{count} {label}{suffix}")
    if not parts:
        return "A confirmar"
    return f"{total} pessoa{'s' if total != 1 else ''} ({', '.join(parts)})"


def wrap(c: canvas.Canvas, text: str, x: float, y: float, width: float, size=10, leading=14, bold=False) -> float:
    font = "Helvetica-Bold" if bold else "Helvetica"
    c.setFont(font, size)
    words = clean(text).split()
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if c.stringWidth(candidate, font, size) <= width:
            line = candidate
        else:
            c.drawString(x, y, line)
            y -= leading
            line = word
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def box(c: canvas.Canvas, x: float, y: float, w: float, h: float, title: str, body: str) -> None:
    c.setFillColor(colors.HexColor("#F5F7FA"))
    c.setStrokeColor(colors.HexColor("#D7DDE5"))
    c.roundRect(x, y - h, w, h, 6, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#0F3B5F"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 12, y - 18, title.upper())
    c.setFillColor(colors.HexColor("#162433"))
    wrap(c, body, x + 12, y - 36, w - 24, 10, 13)


def generate_budget(data: dict, out_file: str | Path) -> Path:
    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out_path), pagesize=A4)
    width, height = A4
    margin = 42

    client = first_name(value(data, "budget_cliente") or value(data, "cliente"))
    service = value(data, "budget_servico") or value(data, "servico", "Servico privativo")
    included = value(data, "budget_inclusos") or value(data, "servico_detalhe", "Transporte privativo")
    period = value(data, "budget_periodo")
    if not period:
        start = value(data, "data")
        end = value(data, "retorno")
        period = f"Chegada: {start} | Retorno: {end}" if start or end else "A combinar"
    passengers = value(data, "budget_passageiros") or passenger_summary(data)
    total = value(data, "budget_total") or value(data, "cobrar", "A confirmar")
    per_person = value(data, "budget_por_pessoa")
    notes = value(data, "budget_observacoes") or value(data, "obs_venda", "Servico privativo com carro higienizado.")

    c.setFillColor(colors.HexColor("#0F3B5F"))
    c.rect(0, height - 118, width, 118, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 31)
    c.drawString(margin, height - 62, "JPP")
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(colors.HexColor("#D6AE5A"))
    c.drawString(margin + 72, height - 58, "TURISMO")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.white)
    c.drawString(margin + 72, height - 72, "executivo")
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(width - margin, height - 58, "Orcamento")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - margin, height - 76, datetime.now().strftime("%d/%m/%Y"))

    y = height - 154
    c.setFillColor(colors.HexColor("#162433"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, y, f"Ola, {client}!")
    y -= 24
    c.setFont("Helvetica", 11)
    y = wrap(c, "Segue o seu orcamento com a JPP Turismo Executivo.", margin, y, width - 2 * margin, 11, 15)

    y -= 14
    card_w = (width - 2 * margin - 14) / 2
    box(c, margin, y, card_w, 78, "Servico", service)
    box(c, margin + card_w + 14, y, card_w, 78, "Passageiros", passengers)
    y -= 98
    box(c, margin, y, card_w, 78, "Periodo", period)
    box(c, margin + card_w + 14, y, card_w, 78, "Valor total", total)

    y -= 116
    c.setFillColor(colors.HexColor("#0F3B5F"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Servicos incluidos")
    y -= 18
    c.setFillColor(colors.HexColor("#162433"))
    y = wrap(c, included, margin, y, width - 2 * margin, 10, 14)

    if per_person:
        y -= 12
        c.setFillColor(colors.HexColor("#0F3B5F"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "Valor por pessoa")
        y -= 18
        c.setFillColor(colors.HexColor("#162433"))
        y = wrap(c, per_person, margin, y, width - 2 * margin, 10, 14)

    y -= 12
    c.setFillColor(colors.HexColor("#0F3B5F"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Observacoes")
    y -= 18
    c.setFillColor(colors.HexColor("#162433"))
    y = wrap(c, notes, margin, y, width - 2 * margin, 10, 14)

    c.setStrokeColor(colors.HexColor("#D7DDE5"))
    c.line(margin, 76, width - margin, 76)
    c.setFillColor(colors.HexColor("#627083"))
    c.setFont("Helvetica", 8)
    c.drawString(margin, 58, f"CNPJ: {COMPANY['cnpj']} | CADASTUR: {COMPANY['cadastur']}")
    c.drawString(margin, 45, f"{COMPANY['address_1']} - {COMPANY['address_2']}")
    c.drawString(margin, 32, f"{COMPANY['contact']} | {COMPANY['email']}")
    c.save()
    return out_path
