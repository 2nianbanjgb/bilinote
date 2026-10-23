# =============================================================================
# 把导出的笔记 md 里的 /static/screenshots/xxx.jpg 变成本地能看的图片
#
# 用法：
#   .\整理笔记图片.ps1 -MdPath "D:\笔记\某某视频.md"                # 复制图片到同目录，改成相对路径
#   .\整理笔记图片.ps1 -MdPath "..." -Mode url                     # 改成 http://127.0.0.1:3015/... 直接引用
#   .\整理笔记图片.ps1 -MdPath "..." -Mode base64                  # 图片内嵌进 md，单文件，体积大
#   .\整理笔记图片.ps1 -TaskId aa367a2c-...                        # 直接从服务端结果里取正文
#
# 默认不会覆盖原文件，新文件叫 <原名>.local.md
# =============================================================================
param(
    [string]$MdPath,
    [string]$TaskId,
    [ValidateSet('copy', 'url', 'base64')]
    [string]$Mode = 'copy',
    [string]$OutPath
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$shotDir = Join-Path $root 'docker-data\static\screenshots'
$noteDir = Join-Path $root 'docker-data\data\note_results'
$port = 3015

if (-not $MdPath) {
    if (-not $TaskId) { throw '请给 -MdPath（导出的 md 文件）或 -TaskId（服务端任务 id）' }
    $jsonPath = Join-Path $noteDir "$TaskId.json"
    if (-not (Test-Path $jsonPath)) { throw "找不到任务结果：$jsonPath" }
    $obj = Get-Content $jsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $OutPath) { $OutPath = Join-Path (Get-Location) "$TaskId.local.md" }
    $md = $obj.markdown
} else {
    if (-not (Test-Path $MdPath)) { throw "找不到文件：$MdPath" }
    $md = Get-Content $MdPath -Raw -Encoding UTF8
}

$mdDir = if ($OutPath) { Split-Path -Parent $OutPath } else { if ($MdPath) { Split-Path -Parent (Resolve-Path $MdPath) } else { (Get-Location).Path } }
if (-not $mdDir) { $mdDir = (Get-Location).Path }
$baseName = if ($OutPath) { [System.IO.Path]::GetFileNameWithoutExtension($OutPath) }
            elseif ($MdPath) { [System.IO.Path]::GetFileNameWithoutExtension($MdPath) }
            else { $TaskId }
if (-not $OutPath) { $OutPath = Join-Path $mdDir "$baseName.local.md" }

$assetsDirName = $baseName
$assetsDir = Join-Path $mdDir $assetsDirName
$pattern = [regex]'!\[([^\]]*)\]\(/static/screenshots/([^)]+)\)'
$matches = $pattern.Matches($md)
Write-Host "找到 $($matches.Count) 处截图引用"

$copied = 0
$missing = 0
foreach ($m in $matches) {
    $file = $m.Groups[2].Value
    $src = Join-Path $shotDir $file
    switch ($Mode) {
        'url' {
            $newUrl = "http://127.0.0.1:$port/static/screenshots/$file"
            $md = $md.Replace($m.Value, "![$($m.Groups[1].Value)]($newUrl)")
            $copied++
        }
        'base64' {
            if (Test-Path $src) {
                $bytes = [System.IO.File]::ReadAllBytes($src)
                $mime = if ($file -match '\.png$') { 'image/png' } else { 'image/jpeg' }
                $b64 = [Convert]::ToBase64String($bytes)
                $md = $md.Replace($m.Value, "![$($m.Groups[1].Value)](data:$mime;base64,$b64)")
                $copied++
            } else { $missing++ }
        }
        default {
            if (Test-Path $src) {
                if (-not (Test-Path $assetsDir)) { New-Item -ItemType Directory -Path $assetsDir | Out-Null }
                $dst = Join-Path $assetsDir $file
                if (-not (Test-Path $dst)) { Copy-Item $src $dst }
                $rel = "./$assetsDirName/$file"
                $md = $md.Replace($m.Value, "![$($m.Groups[1].Value)]($rel)")
                $copied++
            } else { $missing++ }
        }
    }
}

[System.IO.File]::WriteAllText($OutPath, $md, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "已写出：$OutPath"
Write-Host "模式：$Mode | 处理图片：$copied | 缺失：$missing"
if ($Mode -eq 'copy' -and $copied -gt 0) { Write-Host "图片目录：$assetsDir" }
if ($missing -gt 0) { Write-Host '警告：有图片在 docker-data\static\screenshots 里找不到（可能被手动删过）' -ForegroundColor Yellow }
