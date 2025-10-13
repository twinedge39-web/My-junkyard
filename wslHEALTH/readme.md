# 🧩 wslHEALTH

This directory contains scripts related to **Windows Subsystem for Linux (WSL)** diagnostics and environment checks.  
They are used to monitor and verify the health of current WSL instances.

---

## ⚙️ Purpose
These scripts output detailed information about:
- Windows build and feature status  
- WSL version, kernel, and subsystem configuration  
- Active distributions and runtime state  

Main target: **debugging**, **post-crash verification**, and **system rebuild references**.

---

## ⚠️ Disclaimer
These scripts reflect **my current local environment**.  
They are **not guaranteed to work** on other systems or under different Windows builds.  
Use them as reference materials or templates — **run at your own risk.**

---

## 🧪 Example
Run the following from PowerShell:

```powershell
.\WSLchecker.ps1
```

It will generate a short system health report similar to:

=== Windows Build ===
Edition: Professional
DisplayVersion: 25H2
Build: 26200

**Created by:** twinedge39-web  
**Last updated:** (auto-sync with current repo commit)

---
