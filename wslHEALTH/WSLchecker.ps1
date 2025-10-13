# --- 直前：エンコーディングとエラー ---
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding            = [System.Text.UTF8Encoding]::new()
chcp 65001 | Out-Null
$ErrorActionPreference = 'Stop'

# 保存先（必要なら変えてOK）
$stamp   = (Get-Date).ToString('yyyyMMdd-HHmmss')
$report  = "$([Environment]::GetFolderPath('Desktop'))\wsl_health_$stamp.txt"

function Write-Block($title, $content) {
  Add-Content -Path $report -Value "`n=== $title ===`n$content"
}

"WSL Health Report  $stamp" | Out-File -Encoding UTF8 $report

# Windows/WSL 版数・機能
$osVer = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
$winFeat = Get-WindowsOptionalFeature -Online |
  Where-Object {$_.FeatureName -in 'Microsoft-Windows-Subsystem-Linux','VirtualMachinePlatform'} |
  Format-Table FeatureName, State -Auto | Out-String

# --- WSLのUTF-16出力をUTF-8文字列に正規化するヘルパ ---
function Normalize-Out([string]$s) {
  if ($null -eq $s) { return "" }
  # UTF-16の片割れ 0x00 (NUL) を除去して純テキスト化
  return ($s -replace "`0","")
}

Write-Block "Windows Build"     ("Edition: {0}`nDisplayVersion: {1}`nBuild: {2}" -f $osVer.EditionID,$osVer.DisplayVersion,$osVer.CurrentBuildNumber)
Write-Block "Windows Features"  $winFeat

# --- WSLのテキスト出力をUTF-16LEとして確実に読み、UTF-8文字列へ整形 ---
function Get-WslText([string]$arguments) {
  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName  = 'wsl.exe'
  $psi.Arguments = $arguments
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  $psi.UseShellExecute        = $false
  $psi.StandardOutputEncoding = [System.Text.Encoding]::Unicode
  $psi.StandardErrorEncoding  = [System.Text.Encoding]::Unicode
  $p = [System.Diagnostics.Process]::Start($psi)
  $out = $p.StandardOutput.ReadToEnd()
  $err = $p.StandardError.ReadToEnd()
  $p.WaitForExit()
  return (($out + $err) -replace "`0","")
}

$wslVersion = Get-WslText '--version'
$wslStatus  = Get-WslText '--status'
$wslListV   = Get-WslText '-l -v'

Write-Block "wsl --version" $wslVersion
Write-Block "wsl --status"  $wslStatus
Write-Block "wsl -l -v"     $wslListV


# 既定ディストロのみで回す（名前は使わない）
$distros = @('DEFAULT_ONLY')
$use_default_only = $true
Write-Host "Detected distro: [DEFAULT (wsl --status の既定を使用)]"

# --- bash本文 ---
$bash = @'
set -e
echo "---- Distro Overview ----"
if command -v lsb_release >/dev/null 2>&1; then
  lsb_release -a 2>/dev/null || true
fi
[ -f /etc/os-release ] && cat /etc/os-release | egrep "^(NAME|VERSION|PRETTY_NAME)=" || true
uname -a
id

echo
echo "---- Package Manager ----"
( command -v apt    && echo apt )    || \
( command -v dnf    && echo dnf )    || \
( command -v pacman && echo pacman ) || \
( command -v zypper && echo zypper ) || echo "unknown"

echo
echo "---- Toolchain Presence ----"
for c in gcc g++ clang make cmake ninja pkg-config ld ar strip git curl wget bsdtar 7z; do
  printf "%-12s : " "$c"
  if command -v "$c" >/dev/null 2>&1; then
    "$c" --version 2>&1 | head -n1
  else
    echo "not found"
  fi
done

echo
echo "---- Dev Packages (deb/rpm) ----"
if command -v dpkg >/dev/null 2>&1; then
  dpkg -l | egrep -i "build-essential|linux-headers|libc6-dev|g\+\+|clang|cmake|ninja-build|pkg-config|fuse3|libfuse3|libfuse-dev" || true
elif command -v rpm >/dev/null 2>&1; then
  rpm -qa | egrep -i "gcc|glibc-headers|kernel-headers|make|cmake|ninja|pkgconf|fuse3|fuse3-libs|fuse-devel" || true
fi

echo
echo "---- Kernel Capabilities ----"
echo -n "binfmt_misc: "; (cat /proc/sys/fs/binfmt_misc/status 2>/dev/null) || echo "unavailable"
[ -e /dev/fuse ] && echo "/dev/fuse present" || echo "/dev/fuse missing"
ls -l /dev/loop* 2>/dev/null || echo "no loop devices detected"

echo
echo "---- Mounts (top 20) ----"
mount | head -n 20

echo
echo "---- Filesystem for Windows mounts ----"
mount | egrep "/mnt/[a-z] " || true

echo
echo "---- WSL Hints ----"
if [ -f /etc/wsl.conf ]; then
  echo "[/etc/wsl.conf]"
  cat /etc/wsl.conf
else
  echo "/etc/wsl.conf not found"
fi

echo
echo "---- Sanity checks for ISO/BIN workflows ----"
printf "fuseiso: ";  command -v fuseiso >/dev/null 2>&1  && echo yes || echo no
printf "archivemount: "; command -v archivemount >/dev/null 2>&1 && echo yes || echo no
printf "7z: "; command -v 7z >/dev/null 2>&1 && echo yes || echo no
printf "bsdtar: "; command -v bsdtar >/dev/null 2>&1 && echo yes || echo no

echo
echo "---- Permissions quick check ----"
groups
[ -r /etc/fuse.conf ] && (echo "[/etc/fuse.conf]"; cat /etc/fuse.conf) || echo "/etc/fuse.conf not readable or missing"

echo
echo "---- Done ----"
'@



# --- 直前：エンコーディングとエラー ---
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding            = [System.Text.UTF8Encoding]::new()
chcp 65001 | Out-Null
$ErrorActionPreference = 'Stop'

# 保存先（必要なら変えてOK）
$stamp   = (Get-Date).ToString('yyyyMMdd-HHmmss')
$report  = "$([Environment]::GetFolderPath('Desktop'))\wsl_health_$stamp.txt"

function Write-Block($title, $content) {
  Add-Content -Path $report -Value "`n=== $title ===`n$content"
}

"WSL Health Report  $stamp" | Out-File -Encoding UTF8 $report

# Windows/WSL 版数・機能
$osVer = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
$winFeat = Get-WindowsOptionalFeature -Online |
  Where-Object {$_.FeatureName -in 'Microsoft-Windows-Subsystem-Linux','VirtualMachinePlatform'} |
  Format-Table FeatureName, State -Auto | Out-String

# --- WSLのUTF-16出力をUTF-8文字列に正規化するヘルパ ---
function Normalize-Out([string]$s) {
  if ($null -eq $s) { return "" }
  # UTF-16の片割れ 0x00 (NUL) を除去して純テキスト化
  return ($s -replace "`0","")
}

Write-Block "Windows Build"     ("Edition: {0}`nDisplayVersion: {1}`nBuild: {2}" -f $osVer.EditionID,$osVer.DisplayVersion,$osVer.CurrentBuildNumber)
Write-Block "Windows Features"  $winFeat

# --- WSLのテキスト出力をUTF-16LEとして確実に読み、UTF-8文字列へ整形 ---
function Get-WslText([string]$arguments) {
  $psi = [System.Diagnostics.ProcessStartInfo]::new()
  $psi.FileName  = 'wsl.exe'
  $psi.Arguments = $arguments
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  $psi.UseShellExecute        = $false
  $psi.StandardOutputEncoding = [System.Text.Encoding]::Unicode
  $psi.StandardErrorEncoding  = [System.Text.Encoding]::Unicode
  $p = [System.Diagnostics.Process]::Start($psi)
  $out = $p.StandardOutput.ReadToEnd()
  $err = $p.StandardError.ReadToEnd()
  $p.WaitForExit()
  return (($out + $err) -replace "`0","")
}

$wslVersion = Get-WslText '--version'
$wslStatus  = Get-WslText '--status'
$wslListV   = Get-WslText '-l -v'

Write-Block "wsl --version" $wslVersion
Write-Block "wsl --status"  $wslStatus
Write-Block "wsl -l -v"     $wslListV


# 既定ディストロのみで回す（名前は使わない）
$distros = @('DEFAULT_ONLY')
$use_default_only = $true
Write-Host "Detected distro: [DEFAULT (wsl --status の既定を使用)]"

# --- bash本文 ---
$bash = @'
set -e
echo "---- Distro Overview ----"
if command -v lsb_release >/dev/null 2>&1; then
  lsb_release -a 2>/dev/null || true
fi
[ -f /etc/os-release ] && cat /etc/os-release | egrep "^(NAME|VERSION|PRETTY_NAME)=" || true
uname -a
id

echo
echo "---- Package Manager ----"
( command -v apt    && echo apt )    || \
( command -v dnf    && echo dnf )    || \
( command -v pacman && echo pacman ) || \
( command -v zypper && echo zypper ) || echo "unknown"

echo
echo "---- Toolchain Presence ----"
for c in gcc g++ clang make cmake ninja pkg-config ld ar strip git curl wget bsdtar 7z; do
  printf "%-12s : " "$c"
  if command -v "$c" >/dev/null 2>&1; then
    "$c" --version 2>&1 | head -n1
  else
    echo "not found"
  fi
done

echo
echo "---- Dev Packages (deb/rpm) ----"
if command -v dpkg >/dev/null 2>&1; then
  dpkg -l | egrep -i "build-essential|linux-headers|libc6-dev|g\+\+|clang|cmake|ninja-build|pkg-config|fuse3|libfuse3|libfuse-dev" || true
elif command -v rpm >/dev/null 2>&1; then
  rpm -qa | egrep -i "gcc|glibc-headers|kernel-headers|make|cmake|ninja|pkgconf|fuse3|fuse3-libs|fuse-devel" || true
fi

echo
echo "---- Kernel Capabilities ----"
echo -n "binfmt_misc: "; (cat /proc/sys/fs/binfmt_misc/status 2>/dev/null) || echo "unavailable"
[ -e /dev/fuse ] && echo "/dev/fuse present" || echo "/dev/fuse missing"
ls -l /dev/loop* 2>/dev/null || echo "no loop devices detected"

echo
echo "---- Mounts (top 20) ----"
mount | head -n 20

echo
echo "---- Filesystem for Windows mounts ----"
mount | egrep "/mnt/[a-z] " || true

echo
echo "---- WSL Hints ----"
if [ -f /etc/wsl.conf ]; then
  echo "[/etc/wsl.conf]"
  cat /etc/wsl.conf
else
  echo "/etc/wsl.conf not found"
fi

echo
echo "---- Sanity checks for ISO/BIN workflows ----"
printf "fuseiso: ";  command -v fuseiso >/dev/null 2>&1  && echo yes || echo no
printf "archivemount: "; command -v archivemount >/dev/null 2>&1 && echo yes || echo no
printf "7z: "; command -v 7z >/dev/null 2>&1 && echo yes || echo no
printf "bsdtar: "; command -v bsdtar >/dev/null 2>&1 && echo yes || echo no

echo
echo "---- Permissions quick check ----"
groups
[ -r /etc/fuse.conf ] && (echo "[/etc/fuse.conf]"; cat /etc/fuse.conf) || echo "/etc/fuse.conf not readable or missing"

echo
echo "---- Done ----"
'@

# --- Base64 で本文を書き出して実行（安全） ---
$bashB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($bash))
$bashCmd = @"
set -e
tmp=/tmp/wsl_health.sh
printf '%s' '$bashB64' | base64 -d > "$tmp"
chmod +x "$tmp"
bash "$tmp"
"@


# --- PowerShell→WSL：Base64 で本文を渡して実行（テンポラリファイル不要） ---
$header  = "### Distro: (default) ###"
$content = ""
$exit    = $null

# BASH 本文を UTF-8 → Base64 に
$bashB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($bash))

# BASH本文を Base64 に
$bashB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($bash))

# ★ PowerShell で壊れないように、単一行＋単一引用符で組み立てる（$は展開されない）
$cmd = 'set -e; ' +
       'tmp=$(mktemp /tmp/wsl_health.XXXXXX.sh); ' +
       'printf ''%s'' ''' + $bashB64 + ''' | base64 -d > "$tmp"; ' +
       'chmod +x "$tmp"; ' +
       'bash "$tmp"; ' +
       'rm -f "$tmp"'

# --- PowerShell→WSL 実行（PS5/PS7 両対応・テンポラリなし） ---
$header = "### Distro: (default) ###"

# BASH 本文を Base64（UTF-8）化
$bashB64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($bash))

# bash -lc に渡すワンライナー
$cmd = "set -e; printf '%s' '$bashB64' | base64 -d | bash -e"

# wsl.exe 起動準備（PS5 は Arguments、PS7 は ArgumentList）
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "wsl.exe"
# PS7 なら ArgumentList が使えるが、PS5 でも動くように Arguments 文字列を組む
$psi.Arguments = "-- bash -lc " + ('"{0}"' -f $cmd)  # ←ここがクロスバージョン対応の肝
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError  = $true
$psi.UseShellExecute        = $false
$psi.CreateNoWindow         = $true
# bash 側は UTF-8 で出す前提
$psi.StandardOutputEncoding = [Text.Encoding]::UTF8
$psi.StandardErrorEncoding  = [Text.Encoding]::UTF8

$p = [System.Diagnostics.Process]::Start($psi)
$stdout = $p.StandardOutput.ReadToEnd()
$stderr = $p.StandardError.ReadToEnd()
$p.WaitForExit()
$exit   = $p.ExitCode

$content = "ExitCode: $exit`n" + $stdout
if ($stderr) { $content += "`n[stderr]`n$stderr" }
Write-Block $header $content




Write-Host "レポートを出力しました → $report"

