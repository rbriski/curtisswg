#!/usr/bin/env python3
"""
Generate the Curtiss Ave holiday tree order flyer: one letter-size page with the
ordering details up top and a tear-off order slip at the bottom.

Usage:
    python3 _scripts/order_form.py                # writes CurtissAve.OrderForm.<YEAR>.pdf in the repo root
    python3 _scripts/order_form.py out.pdf        # custom output path

Edit the CONSTANTS block each year (prices, dates, beneficiary). Block captain name,
address, email, phone and Venmo come from _scripts/.env (gitignored, keys in .env.example).
Needs reportlab (installed system-wide here) and the DejaVu / Liberation fonts from Ubuntu.
"""
import sys
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

# ----------------------------------------------------------------- CONSTANTS
YEAR = 2026
TREE_PRICE = 30
REBAR_PRICE = 7
ORDER_DEADLINE = "Friday, November 6"
DELIVERY_DAY = "Saturday, December 5"
SITE = "curtisswg.com"
SITE_URL = "https://curtisswg.com"

# Personal details are deliberately NOT in this file (the repo is public). They are read
# from _scripts/.env, which is gitignored; see _scripts/.env.example for the keys.
ENV_FILE = Path(__file__).resolve().parent / ".env"


def load_env(path):
    values = {}
    if path.exists():
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip().strip('"').strip("'")
    return values


_env = load_env(ENV_FILE)
_PLACEHOLDERS = {
    "CAPTAIN_NAME": "[block captain name]",
    "CAPTAIN_FIRST": "[first name]",
    "CAPTAIN_ADDRESS": "[house number] Curtiss Ave",
    "CAPTAIN_EMAIL": "[email]",
    "CAPTAIN_PHONE": "[phone]",
    "CAPTAIN_VENMO": "[@venmo]",
}
_missing = [k for k in _PLACEHOLDERS if not _env.get(k)]
if _missing:
    print(f"warning: {ENV_FILE} is missing {', '.join(_missing)}; printing placeholders", file=sys.stderr)
CAPTAIN = _env.get("CAPTAIN_NAME") or _PLACEHOLDERS["CAPTAIN_NAME"]
CAPTAIN_FIRST = _env.get("CAPTAIN_FIRST") or _PLACEHOLDERS["CAPTAIN_FIRST"]
ADDRESS = _env.get("CAPTAIN_ADDRESS") or _PLACEHOLDERS["CAPTAIN_ADDRESS"]
EMAIL = _env.get("CAPTAIN_EMAIL") or _env.get("GMAIL_EMAIL") or _PLACEHOLDERS["CAPTAIN_EMAIL"]
PHONE = _env.get("CAPTAIN_PHONE") or _PLACEHOLDERS["CAPTAIN_PHONE"]
VENMO = _env.get("CAPTAIN_VENMO") or _PLACEHOLDERS["CAPTAIN_VENMO"]
BENEFICIARY = "Jeannessa’s Friends"
BENEFICIARY_BLURB = (
    "a memorial foundation that funds veterinary scholarships, pet-rescue grants and "
    "emergency vet care for families in need"
)
MATCH = "$50"
YEARS = YEAR - 1950

# ------------------------------------------------------------------- COLORS
RED = HexColor("#8B1D1D")
GREEN = HexColor("#2F6B3A")
GREEN_LIGHT = HexColor("#4E8F5A")
CREAM = HexColor("#FBF7EC")
INK = HexColor("#333333")
MUTED = HexColor("#6B6B6B")
RULE = HexColor("#BBBBBB")
SHADE = HexColor("#EFEFEF")
TRUNK = HexColor("#6B4A2B")
LIGHTS = [HexColor("#D93025"), HexColor("#1A73E8"), HexColor("#F9AB00"), HexColor("#E8710A")]

PAGE_W, PAGE_H = letter
MARGIN = 36
CONTENT_W = PAGE_W - 2 * MARGIN


def register_fonts():
    dv = Path("/usr/share/fonts/truetype/dejavu")
    lib = Path("/usr/share/fonts/truetype/liberation")
    pdfmetrics.registerFont(TTFont("DejaVuSans", dv / "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", dv / "DejaVuSans-Bold.ttf"))
    if (lib / "LiberationSans-Regular.ttf").exists():
        faces = {
            "Body": "LiberationSans-Regular.ttf",
            "Body-Bold": "LiberationSans-Bold.ttf",
            "Body-Italic": "LiberationSans-Italic.ttf",
            "Body-BoldItalic": "LiberationSans-BoldItalic.ttf",
        }
        for name, file in faces.items():
            pdfmetrics.registerFont(TTFont(name, lib / file))
    else:  # DejaVu fallback (no italic faces needed for this flyer)
        pdfmetrics.registerFont(TTFont("Body", dv / "DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont("Body-Bold", dv / "DejaVuSans-Bold.ttf"))
        pdfmetrics.registerFont(TTFont("Body-Italic", dv / "DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont("Body-BoldItalic", dv / "DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFontFamily(
        "Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-BoldItalic"
    )


def style(size, leading=None, bold=False, color=INK, align=None, space_after=0):
    return ParagraphStyle(
        name=f"s{size}{bold}{color}",
        fontName="Body-Bold" if bold else "Body",
        fontSize=size,
        leading=leading or size * 1.25,
        textColor=color,
        alignment=align if align is not None else 0,
        spaceAfter=space_after,
    )


def para(c, text, x, y_top, width, st):
    """Draw a wrapped paragraph with its top edge at y_top. Returns the height used."""
    p = Paragraph(text, st)
    _, h = p.wrap(width, 2000)
    p.drawOn(c, x, y_top - h)
    return h


def draw_tree(c, x, base_y, h, fill):
    """A simple stacked-triangle tree with a white light on top and colored lights."""
    trunk_h, trunk_w = h * 0.12, h * 0.1
    c.setFillColor(TRUNK)
    c.rect(x - trunk_w / 2, base_y, trunk_w, trunk_h, stroke=0, fill=1)
    body_h = h - trunk_h
    step, tier_h = body_h * 0.28, body_h * 0.44
    light_spots = []
    for i in range(3):
        y = base_y + trunk_h + i * step
        w = h * 0.78 * (1 - 0.22 * i)
        p = c.beginPath()
        p.moveTo(x - w / 2, y)
        p.lineTo(x + w / 2, y)
        p.lineTo(x, y + tier_h)
        p.close()
        c.setFillColor(fill)
        c.drawPath(p, stroke=0, fill=1)
        ly = y + tier_h * 0.22
        lw = w * (1 - 0.22) * 0.8
        for k, frac in enumerate((-0.33, 0.0, 0.33)):
            light_spots.append((x + frac * lw, ly + (k % 2) * tier_h * 0.08, LIGHTS[(i + k) % len(LIGHTS)]))
    for lx, ly, col in light_spots:
        c.setFillColor(col)
        c.circle(lx, ly, h * 0.022, stroke=0, fill=1)
    top = base_y + h
    c.setFillColor(HexColor("#FFF3B0"))
    c.circle(x, top, h * 0.06, stroke=0, fill=1)
    c.setFillColor(white)
    c.circle(x, top, h * 0.035, stroke=0, fill=1)


def draw_qr(c, url, x, y, size):
    widget = QrCodeWidget(url)
    b = widget.getBounds()
    bw, bh = b[2] - b[0], b[3] - b[1]
    d = Drawing(size, size, transform=[size / bw, 0, 0, size / bh, 0, 0])
    d.add(widget)
    renderPDF.draw(d, c, x, y)


def dashed_cut_line(c, y):
    c.setStrokeColor(MUTED)
    c.setLineWidth(0.8)
    c.setDash(5, 4)
    c.line(MARGIN + 18, y, PAGE_W - MARGIN, y)
    c.setDash()
    face = pdfmetrics.getFont("DejaVuSans").face
    if 0x2702 in face.charToGlyph:  # scissors glyph available
        c.setFont("DejaVuSans", 11)
        c.setFillColor(MUTED)
        c.drawString(MARGIN, y - 4, "✂")
    c.setFont("Body", 7.5)
    c.setFillColor(MUTED)
    c.drawRightString(PAGE_W - MARGIN, y + 3, "cut here and return the slip")


def build(out_path):
    register_fonts()
    c = canvas.Canvas(str(out_path), pagesize=letter)
    c.setTitle(f"Curtiss Ave Holiday Trees {YEAR}")
    c.setAuthor(CAPTAIN)

    # ---------------------------------------------------------------- header
    y = PAGE_H - MARGIN
    c.setFillColor(RED)
    c.setFont("Body-Bold", 26)
    c.drawString(MARGIN, y - 24, "Willow Glen Holiday Trees")
    c.setFillColor(GREEN)
    c.setFont("Body-Bold", 14)
    c.drawString(MARGIN, y - 44, f"Curtiss Avenue  ·  {YEAR}")
    for tx, th, col in ((PAGE_W - MARGIN - 112, 40, GREEN_LIGHT), (PAGE_W - MARGIN - 70, 56, GREEN), (PAGE_W - MARGIN - 28, 44, GREEN_LIGHT)):
        draw_tree(c, tx, y - 58, th, col)
    c.setStrokeColor(RED)
    c.setLineWidth(1.2)
    c.line(MARGIN, y - 62, PAGE_W - MARGIN, y - 62)

    # ------------------------------------------------------ order call-to-action
    box_top = y - 70
    pad = 14
    qr_size = 88
    qr_x = PAGE_W - MARGIN - 16 - qr_size
    tx = MARGIN + 16
    tw = qr_x - 14 - tx
    lines = [
        (f"Order your tree by {ORDER_DEADLINE}", style(18, 21, bold=True, color=GREEN), 6),
        (f"<b>Trees ${TREE_PRICE} each</b> &nbsp;\u00b7&nbsp; <b>Rebar ${REBAR_PRICE} each</b> "
         f"(optional, keeps the tree upright)", style(10.5, 14), 0),
        (f"<b>Delivery {DELIVERY_DAY}</b>", style(10.5, 14), 7),
        ("Two ways to order:", style(10.5, 13, bold=True), 1),
        (f"<b>1.</b> Online in a minute at <b>{SITE}</b> (or scan the code).", style(10.5, 13.5), 0),
        (f"<b>2.</b> Fill out the slip at the bottom and drop it at <b>{ADDRESS}</b>, "
         f"or just text or email {CAPTAIN_FIRST} your order.", style(10.5, 13.5), 0),
    ]
    paras = [(Paragraph(t, st), gap) for t, st, gap in lines]
    text_h = sum(p.wrap(tw, 2000)[1] + gap for p, gap in paras)
    box_h = max(text_h + 2 * pad, qr_size + 16 + 14 + 16)
    c.setFillColor(CREAM)
    c.setStrokeColor(GREEN)
    c.setLineWidth(1.6)
    c.roundRect(MARGIN, box_top - box_h, CONTENT_W, box_h, 8, stroke=1, fill=1)

    qr_y = box_top - 16 - qr_size
    draw_qr(c, SITE_URL, qr_x, qr_y, qr_size)
    c.setFont("Body-Bold", 8)
    c.setFillColor(GREEN)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 11, "scan to order online")

    ty = box_top - pad
    for para_obj, gap in paras:
        _, h = para_obj.wrap(tw, 2000)
        para_obj.drawOn(c, tx, ty - h)
        ty -= h + gap

    # ----------------------------------------------------------- two columns
    col_top = box_top - box_h - 16
    col_w = (CONTENT_W - 24) / 2
    lx, rx = MARGIN, MARGIN + col_w + 24
    head = style(11.5, 14, bold=True, color=GREEN)
    body = style(10, 13.2)
    small = style(8.6, 11, color=MUTED)

    ly = col_top
    ly -= para(c, "Your block captain", lx, ly, col_w, head)
    ly -= 3
    ly -= para(c, f"<b>{CAPTAIN}</b> · {ADDRESS}", lx, ly, col_w, body)
    ly -= para(c, f"{EMAIL}", lx, ly, col_w, body)
    ly -= para(c, f"{PHONE} · call or text", lx, ly, col_w, body)
    ly -= 10
    ly -= para(c, "Payment", lx, ly, col_w, head)
    ly -= 3
    ly -= para(
        c,
        f"Venmo <b>{VENMO}</b>, PayPal <b>{EMAIL}</b>, or cash or check made out to {CAPTAIN}. "
        f"Pay with your order or when your tree arrives, whichever is easier.",
        lx, ly, col_w, body,
    )
    ly -= 10
    ly -= para(c, "Delivery and set-up", lx, ly, col_w, head)
    ly -= 3
    ly -= para(
        c,
        f"{CAPTAIN_FIRST} delivers along Curtiss on {DELIVERY_DAY} (the day the trees arrive). "
        f"Need a hand getting it into the ground? Check the box on the slip.",
        lx, ly, col_w, body,
    )

    ry = col_top
    ry -= para(c, "The tradition", rx, ry, col_w, head)
    ry -= 3
    ry -= para(
        c,
        f"In 1950, Willow Glen neighbors began placing a lighted tree in every front yard, and "
        f"{YEARS} years later the tradition continues. Trees are 4 to 6 feet tall, placed about "
        f"10 feet from the sidewalk, with one white light at the top and large multi-colored "
        f"lights throughout. Decorate yours however you like, the point is to light up Curtiss "
        f"from end to end.",
        rx, ry, col_w, body,
    )
    ry -= 10
    ry -= para(c, "Giving back (optional)", rx, ry, col_w, style(9.5, 12, bold=True, color=MUTED))
    ry -= 2
    ry -= para(
        c,
        f"Trees cost less than half of market value. If you like, add a donation to this "
        f"year’s beneficiary, <b>{BENEFICIARY}</b>, {BENEFICIARY_BLURB}. "
        f"The Briski family will match donations up to {MATCH}.",
        rx, ry, col_w, small,
    )

    # ---------------------------------------------------------------- cut line
    cut_y = min(ly, ry) - 22
    dashed_cut_line(c, cut_y)

    # --------------------------------------------------------------- order slip
    sy = cut_y - 18
    c.setFillColor(RED)
    c.setFont("Body-Bold", 12)
    c.drawString(MARGIN, sy, f"Curtiss Ave Holiday Tree Order {YEAR}")
    c.setFillColor(INK)
    c.setFont("Body", 9.5)
    c.drawRightString(PAGE_W - MARGIN, sy, f"Return to {CAPTAIN}, {ADDRESS}, by {ORDER_DEADLINE}")

    table_top = sy - 10
    left_w = 340
    right_w = CONTENT_W - left_w
    x0, x1, x2 = MARGIN, MARGIN + left_w, MARGIN + CONTENT_W
    header_h = 17
    footer_room = 30
    row_h = max(26, min(34, (table_top - (MARGIN + footer_room) - header_h) / 7))
    rows = [
        ("Name:", None, row_h),
        ("Address on Curtiss:", "CHECK", row_h),
        ("Email:", "Phone:", row_h),
        ("HEADER", "Amount", header_h),
        (f"# of Trees (${TREE_PRICE} each):", "$", row_h),
        (f"# of Rebar (${REBAR_PRICE} each):", "$", row_h),
        (f"Donation to {BENEFICIARY} (optional):", "$", row_h),
        ("Total:", "$", row_h),
    ]
    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    yy = table_top
    for label, right, h in rows:
        bottom = yy - h
        if label == "HEADER":
            c.setFillColor(SHADE)
            c.rect(x0, bottom, CONTENT_W, h, stroke=0, fill=1)
            c.setFillColor(INK)
            c.setFont("Body-Bold", 9.5)
            c.drawString(x0 + 6, bottom + 5, "Your order")
            c.drawString(x1 + 6, bottom + 5, right)
        else:
            c.setFillColor(INK)
            c.setFont("Body-Bold" if label == "Total:" else "Body", 10)
            if label == "Total:":
                c.drawRightString(x1 - 6, bottom + 9, label)
            else:
                c.drawString(x0 + 6, bottom + h - 13, label)
            if right == "CHECK":
                c.rect(x1 + 6, bottom + h - 16, 9, 9, stroke=1, fill=0)
                c.setFont("Body", 9)
                c.drawString(x1 + 19, bottom + h - 14.5, "I need help getting / setting up my tree")
            elif right == "$":
                c.setFont("Body", 10)
                c.drawString(x1 + 6, bottom + 9, "$")
            elif right:
                c.setFont("Body", 10)
                c.drawString(x1 + 6, bottom + h - 13, right)
        c.rect(x0, bottom, CONTENT_W, h, stroke=1, fill=0)
        if right is not None:
            c.line(x1, bottom, x1, yy)
        yy = bottom

    c.setFont("Body", 8.2)
    c.setFillColor(MUTED)
    c.drawCentredString(
        PAGE_W / 2, yy - 13,
        f"Venmo {VENMO}  ·  PayPal {EMAIL}  ·  cash or check  ·  questions? {PHONE}  ·  "
        f"skip the paper: {SITE}",
    )
    c.showPage()
    c.save()
    return out_path


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / f"CurtissAve.OrderForm.{YEAR}.pdf"
    build(out)
    print(f"wrote {out}")
