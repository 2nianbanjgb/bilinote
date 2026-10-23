# 注册 bilinote:// 协议，让网页里的「导出目录」按钮能直接打开成品目录
# 只写 HKCU（当前用户），不需要管理员权限。
#
#   .\注册导出目录协议.ps1            # 注册（默认指向本目录下的 bilinote_output_docs）
#   .\注册导出目录协议.ps1 -Dir "D:\其他\目录"
#   .\注册导出目录协议.ps1 -Unregister
param(
    [string]$Dir,
    [switch]$Unregister
)

$key = 'HKCU:\Software\Classes\bilinote'

if ($Unregister) {
    Remove-Item $key -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host '已移除 bilinote:// 协议'
    return
}

if (-not $Dir) { $Dir = Join-Path $PSScriptRoot 'bilinote_output_docs' }
if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }

New-Item -Path $key -Force | Out-Null
Set-ItemProperty -Path $key -Name '(default)' -Value 'URL:BiliNote Export Folder'
New-ItemProperty -Path $key -Name 'URL Protocol' -Value '' -PropertyType String -Force | Out-Null

$cmdKey = "$key\shell\open\command"
New-Item -Path $cmdKey -Force | Out-Null
$command = 'powershell -NoProfile -WindowStyle Hidden -Command "Start-Process ''' + $Dir + '''"'
Set-ItemProperty -Path $cmdKey -Name '(default)' -Value $command

Write-Host "已注册 bilinote:// → $Dir"
Write-Host '在网页里点「导出目录」即可打开（浏览器首次会问一次是否允许）。'