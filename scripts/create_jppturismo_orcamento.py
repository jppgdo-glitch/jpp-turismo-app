from datetime import datetime
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from scripts.create_jppturismo_ordem import COMPANY, clean


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "pdf" / "orcamentos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BLUE = colors.HexColor("#123F61")
GOLD = colors.HexColor("#D6A63D")
INK = colors.HexColor("#172334")
MUTED = colors.HexColor("#62748D")
SOFT = colors.HexColor("#F4F7FB")
LINE = colors.HexColor("#D8E0EA")


def value(data: dict, key: str, default: str = "") -> str:
    return clean(data.get(key), default)


def money_number(text: str) -> float | None:
    match = re.search(r"(\d[\d.]*(?:,\d{2})?)", text or "")
    if not match:
        return None
    return float(match.group(1).replace(".", "").replace(",", "."))


def br_money(amount: float) -> str:
    if amount.is_integer():
        return f"R$ {int(amount):,}".replace(",", ".")
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def greeting_name(name: str) -> str:
    name = clean(name).title()
    return name or "Cliente"


def passenger_counts(data: dict) -> tuple[int, int, int, int, int]:
    values = []
    for key in ["adt", "chd", "inf", "sen", "free"]:
        try:
            values.append(int(value(data, key, "0") or "0"))
        except ValueError:
            values.append(0)
    return tuple(values)


def passenger_summary(data: dict) -> str:
    adt, chd, inf, sen, free = passenger_counts(data)
    total = adt + chd + inf + sen + free
    parts = []
    if adt:
        parts.append(f"{adt} adulto{'s' if adt != 1 else ''}")
    if chd:
        parts.append(f"{chd} criança{'s' if chd != 1 else ''}")
    if inf:
        parts.append(f"{inf} infantil")
    if sen:
        parts.append(f"{sen} sênior{'es' if sen != 1 else ''}")
    if free:
        parts.append(f"{free} free")
    if not total:
        return "A confirmar"
    return f"{total} pessoa{'s' if total != 1 else ''} ({', '.join(parts)})"


def total_passengers(data: dict) -> int:
    return sum(passenger_counts(data))


def wrap(c: canvas.Canvas, text: str, x: float, y: float, width: float, size=10, leading=13, bold=False) -> float:
    font = "Helvetica-Bold" if bold else "Helvetica"
    c.setFont(font, size)
    for paragraph in str(text or "").splitlines() or [""]:
        words = clean(paragraph).split()
        line = ""
        if not words:
            y -= leading
            continue
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


def card(c: canvas.Canvas, x: float, y: float, w: float, h: float, title: str, body: str) -> None:
    c.setFillColor(SOFT)
    c.setStrokeColor(LINE)
    c.roundRect(x, y - h, w, h, 6, stroke=1, fill=1)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 12, y - 20, title.upper())
    c.setFillColor(INK)
    wrap(c, body, x + 12, y - 42, w - 24, 11, 14)


def feature(c: canvas.Canvas, x: float, y: float, title: str, body: str) -> None:
    c.setFillColor(GOLD)
    c.circle(x, y + 2, 3, stroke=0, fill=1)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x + 12, y, title)
    c.setFillColor(INK)
    wrap(c, body, x + 12, y - 14, 210, 9, 12)


def pretty_period(data: dict) -> str:
    explicit = value(data, "budget_periodo")
    if explicit:
        return explicit.replace(" | ", "\n")
    start = value(data, "data")
    end = value(data, "retorno")
    lines = []
    if start:
        date, _, time = start.partition(" ")
        lines.append(f"Chegada: {date}" + (f" às {time.replace(':', 'h')}" if time else ""))
    if end:
        date, _, time = end.partition(" ")
        lines.append(f"Retorno: {date}" + (f" às {time.replace(':', 'h')}" if time else ""))
    return "\n".join(lines) or "A combinar"


def service_title(data: dict) -> str:
    budget_service = value(data, "budget_servico")
    if budget_service:
        return budget_service
    service = value(data, "servico", "Serviço privativo")
    detail = value(data, "servico_detalhe")
    if "transfer" in service.lower():
        suffix = "\n(ida e volta)" if "ida" in detail.lower() or "volta" in detail.lower() else ""
        return f"Transfer privativo POA <-> Gramado/Canela{suffix}"
    return service


def included_text(data: dict) -> str:
    return value(data, "budget_inclusos") or value(
        data,
        "servico_detalhe",
        "Atendimento privativo com motorista, carro higienizado e roteiro personalizado.",
    )


def vehicle_text(data: dict) -> str:
    vehicle = value(data, "veiculo", "Veículo privativo")
    total = total_passengers(data)
    return f"{vehicle} privativo\nConforto para {total or 'seus'} passageiro{'s' if total != 1 else ''}"


def important_info(data: dict) -> str:
    notes = value(data, "budget_observacoes") or value(data, "obs_venda")
    if notes and len(notes) > 16:
        return notes
    return "Para o retorno ao aeroporto, sugerimos a saída com 3h30 de antecedência do horário do voo."


def generate_budget(data: dict, out_file: str | Path) -> Path:
    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(out_path), pagesize=A4)
    c.setTitle(f"Orçamento - {greeting_name(value(data, 'budget_cliente') or value(data, 'cliente'))}")
    c.setAuthor("JPP Turismo Executivo")
    width, height = A4
    margin = 42
    content_w = width - 2 * margin

    client = greeting_name(value(data, "budget_cliente") or value(data, "cliente"))
    service = service_title(data)
    passengers = passenger_summary(data)
    vehicle = value(data, "veiculo", "Veículo privativo")
    vehicle_card = vehicle_text(data)
    period = pretty_period(data)
    total = value(data, "budget_total") or value(data, "cobrar", "A confirmar")
    total_amount = money_number(total)
    total_label = br_money(total_amount) if total_amount is not None else total
    per_person = value(data, "budget_por_pessoa")
    if not per_person and total_amount is not None and total_passengers(data):
        per_person = f"{br_money(total_amount / total_passengers(data))} por pessoa"
    deposit = br_money(total_amount * 0.10) if total_amount is not None else "10% do valor"

    c.setFillColor(BLUE)
    c.rect(0, height - 118, width, 118, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 31)
    c.drawString(margin, height - 62, "JPP")
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(GOLD)
    c.drawString(margin + 72, height - 58, "TURISMO")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.white)
    c.drawString(margin + 72, height - 72, "executivo")
    c.setFont("Helvetica-Bold", 20)
    c.drawRightString(width - margin, height - 58, "Orçamento")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - margin, height - 77, datetime.now().strftime("%d/%m/%Y"))

    y = height - 158
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 19)
    c.drawString(margin, y, f"Olá, {client}!")
    y -= 24
    c.setFont("Helvetica", 11)
    c.drawString(margin, y, "Segue o seu orçamento com a JPP Turismo Executivo.")

    y -= 24
    card_w = (content_w - 14) / 2
    card(c, margin, y, card_w, 72, "Serviço", service)
    card(c, margin + card_w + 14, y, card_w, 72, "Passageiros", f"{passengers}\nVeículo: {vehicle}")
    y -= 86
    card(c, margin, y, card_w, 72, "Período", period)
    card(c, margin + card_w + 14, y, card_w, 72, "Veículo", vehicle_card)

    y -= 96
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Sua experiência inclui")
    y -= 20
    feature(c, margin + 5, y, "Recepção no aeroporto", "Motorista aguardando no desembarque em Porto Alegre.")
    feature(c, margin + 270, y, "Transfer completo", "Aeroporto de Porto Alegre <-> Gramado/Canela.")
    y -= 42
    feature(c, margin + 5, y, f"{vehicle} privativo", f"Conforto e tranquilidade para {total_passengers(data) or 'seus'} passageiros.")
    feature(c, margin + 270, y, "Atendimento personalizado", "Segurança e pontualidade em cada trajeto.")

    y -= 62
    block_h = 82
    c.setFillColor(BLUE)
    c.roundRect(margin, y - block_h, content_w, block_h, 7, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 14, y - 22, "INVESTIMENTO DA EXPERIÊNCIA")
    c.drawRightString(width - margin - 22, y - 22, "VALOR TOTAL")
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 10)
    wrap(c, f"{included_text(data)}\nPacote: {total_label}", margin + 14, y - 44, 280, 10, 13)
    c.setFont("Helvetica-Bold", 20)
    c.drawRightString(width - margin - 22, y - 50, total_label)
    if per_person:
        c.setFont("Helvetica", 9)
        c.drawRightString(width - margin - 22, y - 72, per_person)

    y -= 108
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Informação importante")
    y -= 18
    c.setFillColor(INK)
    y = wrap(c, important_info(data), margin, y, content_w, 10, 13)

    y -= 4
    confirm_h = 56
    c.setFillColor(colors.HexColor("#FFF8EA"))
    c.setStrokeColor(GOLD)
    c.roundRect(margin, y - confirm_h, content_w, confirm_h, 6, stroke=1, fill=1)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 14, y - 20, "CONFIRMAÇÃO DO ATENDIMENTO")
    c.setFillColor(INK)
    wrap(
        c,
        f"Para reservar o atendimento, solicitamos 10% de adiantamento: {deposit}. Após a confirmação do pagamento, o atendimento ficará reservado com a JPP Turismo.",
        margin + 14,
        y - 38,
        content_w - 28,
        9,
        12,
    )

    y -= 80
    c.setFillColor(BLUE)
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, "Será um prazer cuidar dos seus deslocamentos na Serra Gaúcha.")

    c.setStrokeColor(LINE)
    c.line(margin, 76, width - margin, 76)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(margin, 58, f"CNPJ: {COMPANY['cnpj']}  |  CADASTUR: {COMPANY['cadastur']}")
    c.drawString(margin, 45, f"{COMPANY['address_1']} - {COMPANY['address_2']}")
    c.drawString(margin, 32, f"{COMPANY['contact']}  |  {COMPANY['email']}")
    c.save()
    return out_path
