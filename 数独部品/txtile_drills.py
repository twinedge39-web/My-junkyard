import csv

IN="drills.csv"
OUT="drills_print.txt"

def fmt9(s):  # 0を . に
    return " ".join("." if ch=="0" else ch for ch in s)

with open(IN, newline="", encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as o:
    r = csv.DictReader(f)
    for row in r:
        g = row["grid81"].strip()
        if len(g) != 81:
            continue
        o.write(f'[{row["id"]}] {row.get("note","")}\n')
        for i in range(9):
            o.write(fmt9(g[i*9:(i+1)*9]) + "\n")
        o.write("\n")

print("Wrote drills_print.txt")
