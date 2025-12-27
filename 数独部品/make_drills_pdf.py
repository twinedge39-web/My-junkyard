import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

IN_CSV = "drills.csv"
OUT_PDF = "drills.pdf"

def draw_grid(c, x0, y0, cell=8*mm, bold=0.8, thin=0.4):
    # outer 9x9 lines
    for i in range(10):
        w = bold if i % 3 == 0 else thin
        c.setLineWidth(w)
        # vertical
        c.line(x0 + i*cell, y0, x0 + i*cell, y0 + 9*cell)
        # horizontal
        c.line(x0, y0 + i*cell, x0 + 9*cell, y0 + i*cell)

def draw_numbers(c, grid81, x0, y0, cell=8*mm, font="Helvetica", size=12):
    c.setFont(font, size)
    for r in range(9):
        for col in range(9):
            ch = grid81[r*9 + col]
            if ch == "0":
                continue
            # center text in cell
            x = x0 + col*cell + cell*0.5
            y = y0 + (8-r)*cell + cell*0.35
            c.drawCentredString(x, y, ch)

def main():
    page_w, page_h = A4
    c = canvas.Canvas(OUT_PDF, pagesize=A4)

    # layout
    margin_x = 15*mm
    margin_top = 15*mm
    cell = 9*mm
    grid_size = 9*cell
    line_gap = 6*mm

    # per page: 2 puzzles (縦に2個) くらいが見やすい
    per_page = 2
    y_positions = [
        page_h - margin_top - grid_size - 20*mm,
        page_h - margin_top - (2*grid_size) - 20*mm - 20*mm
    ]

    with open(IN_CSV, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        items = list(r)

    idx = 0
    while idx < len(items):
        c.setFont("Helvetica", 11)

        for slot in range(per_page):
            if idx >= len(items):
                break
            row = items[idx]
            gid = row["id"]
            g = row["grid81"].strip()
            note = row.get("note","")

            # safety: Excel等で壊れた場合
            if len(g) != 81:
                idx += 1
                continue

            x0 = margin_x
            y0 = y_positions[slot]

            # title
            c.drawString(x0, y0 + grid_size + 10*mm, f"{gid}   {note}")

            # grid
            draw_grid(c, x0, y0, cell=cell)
            draw_numbers(c, g, x0, y0, cell=cell, size=13)

            idx += 1

        c.showPage()

    c.save()
    print(f"Wrote {OUT_PDF}")

if __name__ == "__main__":
    main()
