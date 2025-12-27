sudoku_drill_gen.py
        ↓
     drills.csv   ← 原本（触るな）
        ↓
 expand_drills.py
        ↓
drills_expanded.csv  ← Excel用
        ↓
make_drills_pdf.py
        ↓
     drills.pdf  ← 印刷物

（別系統）
drills.csv → sudoku_solve.py（唯一解チェック）



ファイル一覧・簡易説明
🧠 sudoku_solve.py

用途：数独ソルバー（検証用）

役割：

解を探索する

解が1つか／2つ以上あるかを判定

ポイント：

limit=2 で止める → 唯一解チェック専用

将来価値：Sudokuアプリの「品質保証部品」

📄 drills.pdf

用途：印刷用PDF

内容：

数独盤面をA4にレイアウトした完成物

特徴：

フォント・罫線固定

環境差なしで同じ見た目

対象：老母さん・紙で解く用途

🖨 make_drills_pdf.py

用途：CSV → PDF 変換スクリプト

役割：

drills.csv を読み込み

9×9盤面を描画して drills.pdf を生成

ポイント：

ReportLab使用

印刷品質を保証

📝 drills_print.txt

用途：テキスト印刷・確認用

内容：

数独を . 表記で縦に並べたもの

使い道：

内容チェック

PDF化前の簡易確認

🧪 txttile_drills.py

用途：テキスト整形・実験用

役割：

grid81 を人間可読な形に並べる補助

性格：

実験・試作段階のユーティリティ

※ 将来統合 or 消してもOK枠

📊 drills_expanded.csv

用途：Excel安全版データ

内容：

数独1問＝row1〜row9 に分割

目的：

Excelで開いても
81桁壊れない（可逆性確保）

重要度：高（事故防止）

🔧 expand_drills.py









用途：CSV展開ツール

役割：

drills.csv（grid81）
→ drills_expanded.csv（9行形式）

ポイント：

Excel対策の要

📦 drills.csv

用途：数独ドリルの原本

内容：

id

grid81（81文字の0入り盤面）

note（blanks数など）

注意：

Excel直開き厳禁

位置づけ：マスター・データ

🏗 sudoku_drill_gen.py

用途：数独ドリル生成器

役割：

完成盤面生成

空白（blanks）を作る

特徴：

初級向け

single多め設計

将来：難易度調整の起点

📁 puzzles.csv

用途：別バリエーション／試作データ

内容：

過去生成・検証途中の盤面

性格：

保管庫・ジャンク枠

※ 残しておく価値はある