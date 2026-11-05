"""Outils de génération PDF et images pour le corpus fictif."""
import hashlib
import random
from pathlib import Path
from xml.sax.saxutils import escape

import pymupdf
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.graphics.shapes import Circle, Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from corpus_data import BRAND

SS = getSampleStyleSheet()
CELL = ParagraphStyle("cell", parent=SS["BodyText"], fontSize=8, leading=10)
HEAD = ParagraphStyle("head", parent=CELL, fontName="Helvetica-Bold")
BODY = ParagraphStyle("body", parent=SS["BodyText"], fontSize=10, leading=14, spaceAfter=6)


def P(text, style=None):
    return Paragraph(text, style or BODY)


def tbl(rows, widths=None):
    data = [[Paragraph(escape(str(c)), HEAD if r == 0 else CELL) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def chapter(n, title, first=False):
    return ([] if first else [PageBreak()]) + [Paragraph(f"{n}. {escape(title)}", SS["Heading1"])]


def H2(text):
    return Paragraph(escape(text), SS["Heading2"])


def steps(items, start=1):
    """Étapes numérotées ; un AVERTISSEMENT reste dans le même paragraphe que l'étape qu'il concerne."""
    return [P(f"<b>Étape {i}</b> : {t}") for i, t in enumerate(items, start=start)]


def serial(model: str) -> str:
    return f"SN-{int(hashlib.md5(model.encode()).hexdigest()[:8], 16) % 10**8:08d}"


def panel_drawing(model, leds, label):
    d = Drawing(420, 130)
    d.add(Rect(0, 0, 420, 130, strokeColor=colors.black, fillColor=colors.whitesmoke))
    d.add(String(10, 114, f"{label} - Panneau de commande {model}", fontSize=9))
    cmap = {"Vert": colors.green, "Orange": colors.orange, "Rouge": colors.red}
    for i, (lab, _) in enumerate(leds):
        x, y = 40 + (i % 3) * 130, 80 - (i // 3) * 50
        d.add(Circle(x, y, 11, fillColor=cmap[lab.split()[0]], strokeColor=colors.black))
        d.add(String(x - 30, y - 24, lab, fontSize=8))
    return d


def nameplate_drawing(f, label):
    d = Drawing(420, 110)
    d.add(Rect(0, 0, 420, 110, strokeColor=colors.black, fillColor=colors.lightyellow))
    d.add(String(10, 92, f"{label} - Plaque signalétique", fontSize=9))
    lines = [f"{BRAND}  Modèle : {f['model']}", f"Numéro de série : {serial(f['model'])}"]
    if f["family"] == "onduleur":
        lines += [f"Puissance : {f['power_kw']} kW", f"Tension DC max : {f['vdc_max']} V", f"Indice de protection : IP{f['ip']}"]
    else:
        lines += [f"Capacité : {f['capacity_kwh']} kWh", f"Tension nominale : {f['voltage_v']} V", f"Indice de protection : IP{f['ip']}"]
    for i, ln in enumerate(lines):
        d.add(String(14, 74 - i * 14, ln, fontSize=9))
    return d


def build(path, title, flow):
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(40, 22, f"{BRAND} (fictif) - Page {doc.page}")
        canvas.restoreState()

    SimpleDocTemplate(str(path), pagesize=A4, title=title, author=f"{BRAND} (fictif)",
                      leftMargin=45, rightMargin=45, topMargin=50, bottomMargin=45).build(
        [Paragraph(escape(title), SS["Title"])] + flow, onFirstPage=footer, onLaterPages=footer)


def _degrade(img, seed):
    """Défauts de scan reproductibles : légère rotation, ombre de reliure, bruit, flou, contraste."""
    import io
    import random
    rnd = random.Random(seed)
    img = img.convert("L").rotate(rnd.uniform(-1.2, 1.2), expand=False, fillcolor=255, resample=Image.BICUBIC)
    w, h = img.size
    shade = Image.linear_gradient("L").rotate(90).resize((w, h))  # dégradé horizontal
    img = Image.blend(img, Image.composite(img, shade.point(lambda v: 150 + v // 3), Image.new("L", (w, h), 255)), 0.12)
    px = img.load()
    for _ in range(w * h // 90):  # poussière / bruit
        x, y = rnd.randrange(w), rnd.randrange(h)
        px[x, y] = max(0, px[x, y] - rnd.randrange(40, 120))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    return img.point(lambda v: min(255, int(v * 1.04)))


def to_scan(path):
    import io
    src, out = pymupdf.open(path), pymupdf.open()
    for i, pg in enumerate(src):
        pix = pg.get_pixmap(dpi=170)
        img = _degrade(Image.open(io.BytesIO(pix.tobytes("png"))), i)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=65)  # un scan réel est en JPEG
        np_ = out.new_page(width=pg.rect.width, height=pg.rect.height)
        np_.insert_image(np_.rect, stream=buf.getvalue())
    out.save(path)


# ---------- Photos synthétiques avec vérité de terrain ----------
def _font(size):
    for name in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _glow(base, xy, color, radius):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([xy[0] - radius * 2, xy[1] - radius * 2, xy[0] + radius * 2, xy[1] + radius * 2],
                                  fill=color + (140,))
    return Image.alpha_composite(base, layer.filter(ImageFilter.GaussianBlur(radius)))


def render_photo(path, f, variant="normale", lit="Orange fixe", code="E401"):
    """variant : normale | floue | plaque_masquee | sombre. Retourne la vérité de terrain de l'image."""
    W, H = 960, 720
    img = Image.new("RGBA", (W, H), (205, 200, 192, 255))
    d = ImageDraw.Draw(img)
    for y in range(0, H, 4):  # dégradé de mur
        v = 205 - y // 14
        d.rectangle([0, y, W, y + 4], fill=(v, v - 4, v - 10, 255))
    d.rounded_rectangle([108, 88, 868, 668], 28, fill=(60, 60, 60, 120))  # ombre portée
    d.rounded_rectangle([90, 70, 850, 650], 26, fill=(236, 236, 232, 255), outline=(150, 150, 150, 255), width=4)
    model_on_body = variant in ("normale", "sombre")
    if model_on_body:
        d.text((130, 100), f"{BRAND}  {f['model']}", fill=(40, 40, 40, 255), font=_font(34))
    d.rounded_rectangle([130, 170, 520, 330], 10, fill=(18, 40, 30, 255), outline=(90, 90, 90, 255), width=3)  # écran
    d.text((150, 190), code, fill=(120, 255, 170, 255), font=_font(54))
    d.text((150, 262), "ALARME", fill=(120, 255, 170, 255), font=_font(22))
    led_defs = [("Vert fixe", (70, 190, 70)), ("Orange fixe", (255, 150, 0)), ("Rouge fixe", (215, 40, 40))]
    for i, (name, col) in enumerate(led_defs):
        x, y = 620 + i * 70, 250
        on = name == lit
        if on:
            img = _glow(img, (x, y), col, 18)
            d = ImageDraw.Draw(img)
        d.ellipse([x - 20, y - 20, x + 20, y + 20], fill=col + (255,) if on else tuple(v // 3 for v in col) + (255,),
                  outline=(30, 30, 30, 255), width=3)
    plate_legible = variant in ("normale", "sombre")
    d.rectangle([130, 420, 520, 600], fill=(250, 250, 238, 255), outline=(110, 110, 110, 255), width=2)
    fnt = _font(20)
    for i, ln in enumerate([f"{BRAND}", f"Modèle : {f['model']}", f"N° série : {serial(f['model'])}", f"IP{f['ip']}"]):
        d.text((146, 436 + i * 36), ln, fill=(20, 20, 20, 255), font=fnt)
    if variant == "plaque_masquee":
        d.rectangle([126, 470, 524, 560], fill=(30, 30, 30, 255))  # ruban noir sur modèle et série
    d = ImageDraw.Draw(img)
    for sx, sy in ((104, 84), (836, 84), (104, 636), (836, 636)):  # vis de fixation
        d.ellipse([sx - 7, sy - 7, sx + 7, sy + 7], fill=(150, 150, 150, 255), outline=(90, 90, 90, 255))
    for i in range(3):  # câbles qui descendent sous l'appareil
        x = 560 + i * 60
        d.line([x, 650, x + (i - 1) * 14, H], fill=(25, 25, 25, 255), width=14)
    rnd = random.Random(int(hashlib.md5(f"{f['model']}{variant}".encode()).hexdigest()[:6], 16))
    img = img.rotate(rnd.uniform(-2.5, 2.5), resample=Image.BICUBIC, fillcolor=(200, 196, 188, 255))  # cadrage de travers
    veil = Image.new("RGBA", (W, H), (255, 255, 255, 0))  # reflet de fenêtre
    ImageDraw.Draw(veil).polygon([(300, 0), (520, 0), (330, H), (110, H)], fill=(255, 255, 255, 38))
    img = Image.alpha_composite(img, veil.filter(ImageFilter.GaussianBlur(25)))
    noise = Image.effect_noise((W, H), 22).convert("RGBA")  # grain du capteur
    img = Image.blend(img, noise, 0.07)
    out = img.convert("RGB")
    if variant == "floue":
        out = out.filter(ImageFilter.GaussianBlur(11))
    if variant == "sombre":
        out = Image.eval(out, lambda v: int(v * 0.35))
    out.save(path)
    return dict(file=Path(path).name, model=f["model"], variant=variant, led_lit=lit, displayed_code=code,
                plate_legible=plate_legible, model_identifiable=model_on_body and variant == "normale")
