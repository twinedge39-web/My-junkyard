import csv

IN = "drills.csv"
OUT = "drills_expanded.csv"

with open(IN, newline="", encoding="utf-8") as f_in, open(OUT, "w", newline="", encoding="utf-8") as f_out:
    r = csv.DictReader(f_in)
    fieldnames = ["id"] + [f"row{i}" for i in range(1, 10)] + ["note"]
    w = csv.DictWriter(f_out, fieldnames=fieldnames)
    w.writeheader()

    for row in r:
        g = row["grid81"].strip()
        # 念のため：長さが81じゃない場合はスキップ
        if len(g) != 81:
            continue
        out = {"id": row["id"], "note": row.get("note", "")}
        for i in range(9):
            out[f"row{i+1}"] = g[i*9:(i+1)*9]
        w.writerow(out)

print("Wrote drills_expanded.csv")
