# =============================================================================
# 清理 BiliNote 的残留文件
#
# 默认只扫描并列出（dry-run），不会删任何东西。确认无误后加 -Apply 才真删。
#
#   .\清理残留.ps1                 # 只统计/列出
#   .\清理残留.ps1 -Apply          # 真删
#   .\清理残留.ps1 -Apply -KeepDays 7   # 只删 7 天前的（截图除外）
#
# 清理范围：
#   1) static\screenshots 里没有被任何笔记 json 引用的孤儿截图
#   2) data\grid_output、data\output_frames（视频理解/抽帧中间产物）
#   3) data\data 下的 mp3/mp4 临时媒体
#   4) 只有 .status.json、没有结果 json 的失败任务
# =============================================================================
param(
    [switch]$Apply,
    [int]$KeepDays = 0
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$noteDir   = Join-Path $root 'docker-data\data\note_results'
$shotDir   = Join-Path $root 'docker-data\static\screenshots'
$gridDir   = Join-Path $root 'docker-data\data\grid_output'
$framesDir = Join-Path $root 'docker-data\data\output_frames'
$mediaDir  = Join-Path $root 'docker-data\data\data'

function Get-SizeMB($items) {
    if (-not $items) { return 0 }
    [math]::Round((($items | Measure-Object Length -Sum).Sum) / 1MB, 2)
}

# --- 1. 收集所有笔记 json 里引用的截图名 ---
$referenced = New-Object System.Collections.Generic.HashSet[string]
if (Test-Path $noteDir) {
    Get-ChildItem $noteDir -Filter '*.json' | Where-Object { $_.Name -notmatch 'status\.json$|_transcript\.json$|_audio\.json$' } | ForEach-Object {
        try {
            $md = (Get-Content $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json).markdown
            if ($md) {
                [regex]::Matches($md, '/static/screenshots/([^)\s]+)') | ForEach-Object {
                    [void]$referenced.Add($_.Groups[1].Value.Trim())
                }
            }
        } catch { }
    }
}

$cutoff = (Get-Date).AddDays(-$KeepDays)

# --- 2. 孤儿截图 ---
$orphanShots = @()
if (Test-Path $shotDir) {
    $orphanShots = Get-ChildItem $shotDir -File | Where-Object {
        -not $referenced.Contains($_.Name) -and ($KeepDays -eq 0 -or $_.LastWriteTime -lt $cutoff)
    }
}

# --- 3. 抽帧中间产物 ---
$frames = @()
foreach ($d in @($gridDir, $framesDir)) {
    if (Test-Path $d) { $frames += Get-ChildItem $d -File -ErrorAction SilentlyContinue }
}

# --- 4. 临时媒体 ---
$media = @()
if (Test-Path $mediaDir) {
    $media = Get-ChildItem $mediaDir -File | Where-Object { $_.Extension -in '.mp3', '.mp4', '.m4a', '.webm', '.wav' }
}

# --- 5. 失败任务残留 ---
$deadTasks = @()
if (Test-Path $noteDir) {
    $deadTasks = Get-ChildItem $noteDir -Filter '*.status.json' | Where-Object {
        $base = $_.Name -replace '_markdown\.status\.json$', '' -replace '\.status\.json$', ''
        -not (Test-Path (Join-Path $noteDir "$base.json"))
    }
}

Write-Host '=== 残留统计 ==='
Write-Host ("孤儿截图      : {0,5} 个  {1,7} MB  (引用了 {2} 张)" -f $orphanShots.Count, (Get-SizeMB $orphanShots), $referenced.Count)
Write-Host ("抽帧中间产物  : {0,5} 个  {1,7} MB" -f $frames.Count, (Get-SizeMB $frames))
Write-Host ("临时媒体      : {0,5} 个  {1,7} MB" -f $media.Count, (Get-SizeMB $media))
Write-Host ("失败任务残留  : {0,5} 个" -f $deadTasks.Count)
$total = (Get-SizeMB $orphanShots) + (Get-SizeMB $frames) + (Get-SizeMB $media)
Write-Host ("合计可释放    : {0,7} MB" -f $total)

if (-not $Apply) {
    Write-Host ''
    Write-Host '这是 dry-run，什么都没删。确认后加 -Apply 执行：' -ForegroundColor Yellow
    Write-Host '  .\清理残留.ps1 -Apply'
    exit 0
}

Write-Host ''
Write-Host '开始清理...'
foreach ($f in $orphanShots) { Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue }
foreach ($f in $frames)      { Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue }
foreach ($f in $media)       { Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue }
foreach ($f in $deadTasks)   { Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue }

# 清空后的空目录顺手删掉
foreach ($d in @($gridDir, $framesDir)) {
    if ((Test-Path $d) -and -not (Get-ChildItem $d -Force | Select-Object -First 1)) { Remove-Item $d -Force }
}

Write-Host ("完成：删除 {0} 个截图、{1} 个抽帧、{2} 个媒体、{3} 个失败任务记录" -f $orphanShots.Count, $frames.Count, $media.Count, $deadTasks.Count)
