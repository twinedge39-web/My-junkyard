# 🧰 PowerShell Utility Snippets
*PowerShell Utility Scripts for Quick Testing & Registry Integration*  
_Personal collection by twinedge39_  

---

## 🇯🇵 日本語版

このフォルダには、私の環境で動作を確認した PowerShell／レジストリ関連のスクリプトを保管しています。  
環境によって結果が異なる可能性がありますので、**使用は完全に自己責任でお願いします。**

### 🗂 内容

| ファイル名 | 概要 |
|-------------|------|
| **Add-AdminShellHere.reg** | エクスプローラーの右クリックメニューに「PowerShell 7（管理者）」を追加するレジストリ設定。 |
| **support.reg** | PowerShell の拡張設定を行う補助用レジストリ（依存箇所あり）。 |
| **go_ps1file.txt** | PowerShell スクリプトの関連付け／自動実行確認に関するメモ・コマンド群。 |

### 🔒 セキュリティ注意（必読）

- ここにある `.reg` やスクリプトは**直接実行しないでください**。管理者権限が必要で、誤った適用はシステムに影響を与えます。  
- **管理者の明示的承認がない限り実行は禁止**とします。テストは必ず仮想マシンや検証環境で行ってください。  
- 配布物には SHA256 ハッシュを添付してください。ダウンロード後はハッシュを確認し、内容をテキストで必ずレビューしてください。  
- 実行前にレジストリのバックアップ（例：`reg export HKCU backup.reg`）を必ず取ってください。  
- `.reg` は公開リポジトリに生ファイルで置かない（`.reg.txt` とする等）運用を推奨します。

### ⚠️ 注意事項

- これらのスクリプトは **私のローカル環境でのみ検証済み** です。  
  他のPCや異なるWindows構成では動作しない、または問題が発生する可能性があります。  
- `.reg` ファイルの適用には **管理者権限が必要** です。  
  内容を理解したうえで、適用前にバックアップを取ってください。  
- `taskkill /f /im explorer.exe` などのコマンドを含むため、実行中にエクスプローラーが再起動することがあります。  

### 💬 コメント

これらは「一度だけ動かす」「検証に使う」「思いつきを形にした」類のスクリプト群です。  
トラブルが起きた場合でも、GitHub上での責任は一切負いません。  
再現性のある挙動を確認できた場合のみ、改良や共有にご利用ください。

---

## 🇺🇸 English Version

This folder contains PowerShell and registry scripts that were **tested and confirmed to work on my own system**.  
Results may vary depending on your environment — **use entirely at your own risk.**

### 🗂 Contents

| File | Description |
|------|--------------|
| **Add-AdminShellHere.reg** | Adds “PowerShell 7 (Admin)” to the right-click context menu in File Explorer. |
| **support.reg** | Auxiliary registry tweaks for PowerShell behavior and integration. |
| **go_ps1file.txt** | Notes and command snippets for PowerShell file association or script execution checks. |

### 🔒 Security Notice (MUST READ)

- **Do not execute `.reg` or scripts here blindly.** They require admin privileges and can alter system behavior.  
- **Execution is prohibited without explicit admin approval.** Always test in a VM or staging environment first.  
- Provide SHA256 hashes for distributed files. Verify the hash and review the file contents before running.  
- Export the registry before applying changes (e.g., `reg export HKCU backup.reg`).  
- Prefer not to store raw `.reg` files in public repos (use `.reg.txt` or protected distribution channels).

### ⚠️ Disclaimer

- These scripts were verified **only in my personal environment**.  
  They may behave differently or cause issues on other systems or Windows builds.  
- Applying `.reg` files **requires administrator privileges**.  
  Always read and understand the contents, and back up your registry before applying any changes.  
- Some commands (like `taskkill /f /im explorer.exe`) will **restart File Explorer**, which is normal but can interrupt your workflow.  

### 💬 Notes

These are mostly one-off helpers, quick experiments, or half-baked utilities.  
If something breaks, it’s on you — **no warranties or guarantees are provided**.  
Feel free to reuse or improve them if you manage to get consistent results.

---

_© 2025 twinedge39 — Licensed under Apache-2.0_
