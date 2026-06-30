from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "pdf"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "jppturismo_ordem_embarque.pdf"

DEFAULT_DATA = {
    "itinerario": "000001",
    "data": "29/06/2026 08:00",
    "retorno": "29/06/2026 12:00",
    "veiculo": "Van Executiva",
    "operador": "JPP Turismo Executivo",
    "motorista": "A confirmar",
    "guia": "",
    "observacao": "Servico privativo",
    "hora": "08:00",
    "os": "000000",
    "servico": "Aeroporto / Hotel / Passeio",
    "servico_detalhe": "Traslado privativo JPP Turismo",
    "cliente": "CLIENTE EXEMPLO",
    "cliente_detalhe": "CLIENTE EXEMPLO - ADT",
    "destino": "DESTINO / HOTEL",
    "vendedor": "JPP TURISMO",
    "obs_venda": "Servico executivo",
    "adt": "1",
    "chd": "0",
    "inf": "0",
    "sen": "0",
    "free": "0",
    "cobrar": "--",
}


COMPANY = {
    "cnpj": "39.516.309/0001-74",
    "cadastur": "21.370015.44-6",
    "address_1": "Travessa Dois Julio Travi, 75",
    "address_2": "Distrito Industrial - Canela - RS",
    "contact": "CEP: 95680-000 | Tel: (54) 98414-7613",
    "email": "jjppturismoexecutivo@outlook.com",
    "footer": "JPP Turismo Executivo",
}


def br_datetime(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y %H:%M")


def clean(value: object, default: str = "") -> str:
    value = default if value is None else str(value)
    return " ".join(value.strip().split())


def pick(data: dict, key: str) -> str:
    return clean(data.get(key), DEFAULT_DATA.get(key, ""))


def count_text(data: dict) -> str:
    adt = pick(data, "adt") or "0"
    chd = pick(data, "chd") or "0"
    inf = pick(data, "inf") or "0"
    sen = pick(data, "sen") or "0"
    free = pick(data, "free") or "0"
    return f"{adt}({adt}-{chd}-{inf}-{sen}-{free})"


def total_passengers(data: dict) -> int:
    total = 0
    for key in ["adt", "chd", "inf", "sen", "free"]:
        try:
            total += int(pick(data, key) or "0")
        except ValueError:
            pass
    return total


def fit(value: str, max_chars: int) -> str:
    value = clean(value)
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


def draw_qr_placeholder(c: canvas.Canvas, x: float, y: float, size: float) -> None:
    cells = 13
    cell = size / cells
    pattern = {
        (0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2),
        (10, 0), (11, 0), (12, 0), (10, 1), (12, 1), (10, 2), (11, 2), (12, 2),
        (0, 10), (1, 10), (2, 10), (0, 11), (2, 11), (0, 12), (1, 12), (2, 12),
        (4, 1), (6, 1), (8, 1), (5, 3), (7, 3), (9, 3), (3, 5), (5, 5),
        (8, 5), (10, 5), (4, 7), (6, 7), (9, 7), (12, 7), (3, 9), (5, 9),
        (7, 9), (10, 9), (12, 9), (4, 11), (6, 11), (8, 11), (11, 11),
    }
    c.setFillColor(colors.black)
    for row in range(cells):
        for col in range(cells):
            if (col, row) in pattern or ((row * 7 + col * 3) % 11 == 0 and row > 2 and col > 2):
                c.rect(x + col * cell, y + (cells - row - 1) * cell, cell * 0.88, cell * 0.88, stroke=0, fill=1)


def text(c: canvas.Canvas, x: float, y: float, value: str, size=10, bold=False, color=colors.black) -> None:
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, value)


def centered(c: canvas.Canvas, x: float, y: float, value: str, size=10, bold=False) -> None:
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.setFillColor(colors.black)
    c.drawCentredString(x, y, value)


def generate(data: dict | None = None, out_file: str | Path | None = None) -> Path:
    data = {**DEFAULT_DATA, **(data or {})}
    out_path = Path(out_file) if out_file else OUT_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)

    width, height = A4
    c = canvas.Canvas(str(out_path), pagesize=A4)

    margin_x = 20
    top_y = height - 38

    c.setFillColor(colors.HexColor("#103A5C"))
    c.setFont("Helvetica-Bold", 27)
    c.drawString(margin_x, top_y, "JPP")
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#C09643"))
    c.drawString(margin_x + 70, top_y + 2, "TURISMO")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#103A5C"))
    c.drawString(margin_x + 70, top_y - 10, "executivo")

    info_x = 170
    text(c, info_x, top_y + 3, f"CNPJ: {COMPANY['cnpj']}", 9)
    text(c, info_x, top_y - 8, f"CADASTUR: {COMPANY['cadastur']}", 9)
    text(c, info_x, top_y - 19, COMPANY["address_1"], 9)
    text(c, info_x, top_y - 30, COMPANY["address_2"], 9)
    text(c, info_x, top_y - 41, COMPANY["contact"], 9)
    text(c, info_x, top_y - 52, COMPANY["email"], 9)

    centered(c, 452, top_y - 7, "ORDEM DE EMBARQUE", 11)
    centered(c, 452, top_y - 20, "ITINERARIO", 11)
    centered(c, 452, top_y - 33, fit(pick(data, "itinerario"), 12), 11)
    draw_qr_placeholder(c, width - margin_x - 50, top_y - 47, 42)

    c.setStrokeColor(colors.black)
    c.setLineWidth(1.5)
    header_line_y = top_y - 62
    c.line(margin_x, header_line_y, width - margin_x, header_line_y)

    y = header_line_y - 14
    text(c, margin_x, y, "Dados do itinerario - Servico", 11, True)
    y -= 13
    text(c, margin_x, y, "Itinerario", 10, True)
    text(c, margin_x + 49, y, f"{fit(pick(data, 'itinerario'), 12)} -", 10)
    text(c, margin_x + 235, y, "Data:", 10, True)
    text(c, margin_x + 286, y, fit(pick(data, "data"), 18), 10)
    text(c, margin_x + 402, y, "Retorno:", 10, True)
    text(c, margin_x + 458, y, fit(pick(data, "retorno"), 18), 10)

    y -= 16
    text(c, margin_x, y, "Veiculo:", 10, True)
    text(c, margin_x + 49, y, fit(pick(data, "veiculo"), 28), 10)
    text(c, margin_x + 235, y, "Operador", 10, True)
    text(c, margin_x + 286, y, f"{fit(pick(data, 'operador'), 28)} ;", 10)

    y -= 16
    text(c, margin_x, y, "Motorista", 10, True)
    text(c, margin_x + 49, y, fit(pick(data, "motorista"), 28), 10)
    text(c, margin_x + 235, y, "Guia:", 10, True)
    text(c, margin_x + 286, y, fit(pick(data, "guia"), 28), 10)

    y -= 14
    text(c, margin_x, y, "Observacao", 9)
    text(c, margin_x + 72, y, fit(pick(data, "observacao"), 58), 9)

    table_top = y - 19
    table_x = margin_x
    table_w = width - 2 * margin_x
    header_h = 15
    c.setLineWidth(1)
    c.line(table_x, table_top + header_h + 2, table_x + table_w, table_top + header_h + 2)
    c.setFillColor(colors.HexColor("#BDBDBD"))
    c.rect(table_x, table_top, table_w, header_h, stroke=1, fill=1)

    columns = [
        ("Hor", 0),
        ("Nro OS", 30),
        ("Servico", 96),
        ("Cliente", 224),
        ("(ADT-CHD-INF-SEN-FREE)", 397),
        ("Cobrar", 540),
    ]
    for label, dx in columns:
        text(c, table_x + dx, table_top + 4, label, 8 if label.startswith("(") else 10, True)

    row_y = table_top - 13
    text(c, table_x + 2, row_y, fit(pick(data, "hora"), 6), 9)
    text(c, table_x + 30, row_y, fit(pick(data, "os"), 10), 9)
    text(c, table_x + 96, row_y, fit(pick(data, "servico"), 34), 9)
    text(c, table_x + 224, row_y, fit(pick(data, "cliente"), 38), 9)
    text(c, table_x + 430, row_y, fit(count_text(data), 15), 9)
    text(c, table_x + 548, row_y, fit(pick(data, "cobrar"), 4), 9, color=colors.red)

    row_y -= 13
    text(c, table_x + 96, row_y, fit(pick(data, "servico_detalhe"), 34), 9)
    text(c, table_x + 224, row_y, fit(pick(data, "cliente_detalhe"), 38), 9)

    row_y -= 24
    text(c, table_x + 96, row_y, f"> {fit(pick(data, 'destino'), 50)}", 9)

    row_y -= 18
    text(c, table_x, row_y, f"Vend.: {fit(pick(data, 'vendedor'), 22)} | Obs.: {fit(pick(data, 'obs_venda'), 50)}", 9, color=colors.red)
    c.line(table_x, row_y - 5, table_x + table_w, row_y - 5)

    legend_y = row_y - 17
    text(c, table_x, legend_y, "Legenda", 10)
    c.setFillColor(colors.red)
    c.roundRect(table_x + 45, legend_y - 2, 8, 10, 1.5, stroke=0, fill=1)
    text(c, table_x + 47, legend_y, "P", 8, True, colors.white)
    text(c, table_x + 62, legend_y, "- Privativo", 10)
    text(c, table_x + 160, legend_y, f"ADT - {pick(data, 'adt') or '0'}", 10)
    text(c, table_x + 220, legend_y, f"CHD - {pick(data, 'chd') or '0'}", 10)
    text(c, table_x + 280, legend_y, f"INF - {pick(data, 'inf') or '0'}", 10)

    legend_y -= 15
    c.setFillColor(colors.black)
    c.roundRect(table_x + 45, legend_y - 2, 8, 10, 1.5, stroke=0, fill=1)
    text(c, table_x + 47, legend_y, "E", 8, True, colors.white)
    text(c, table_x + 62, legend_y, "- Executivo", 10)
    text(c, table_x + 160, legend_y, f"SEN - {pick(data, 'sen') or '0'}", 10)
    text(c, table_x + 220, legend_y, f"FREE - {pick(data, 'free') or '0'}", 10)
    text(c, table_x + 280, legend_y, f"TOTAL: {total_passengers(data)}", 10)

    footer_y = 42
    text(c, margin_x, footer_y, br_datetime(datetime.now()), 9)
    centered(c, width / 2, footer_y, COMPANY["footer"], 12, True)
    text(c, width - margin_x - 55, footer_y, "Pagina 1 de 1", 9)

    c.save()
    return out_path


if __name__ == "__main__":
    print(generate())
