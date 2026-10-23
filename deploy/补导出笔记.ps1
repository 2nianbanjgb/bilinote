# 把已有笔记补导出到成品目录（bilinote_output_docs）
#
#   .\补导出笔记.ps1 -TaskId bfadf972-...   # 导出一篇
#   .\补导出笔记.ps1 -All                   # 导出全部历史
param(
    [string]$TaskId,
    [switch]$All,
    [int]$Port = 3015
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$noteDir = Join-Path $root 'docker-data\data\note_results'

if (-not $All -and -not $TaskId) { throw '请给 -TaskId 或 -All' }

$ids = @()
if ($All) {
    $ids = Get-ChildItem $noteDir -Filter '*.json' |
        Where-Object { $_.Name -notmatch 'status\.json$|_transcript\.json$|_audio\.json$' } |
        ForEach-Object { $_.BaseName }
} else {
    $ids = @($TaskId)
}

$ok = 0; $fail = 0
foreach ($id in $ids) {
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/export_note/$id" -Method Post -TimeoutSec 60
        if ($r.code -eq 0) { $ok++; Write-Host "OK  $id  $($r.msg)" }
        else { $fail++; Write-Host "FAIL $id  $($r.msg)" }
    } catch {
        $fail++
        Write-Host "ERR  $id  $($_.Exception.Message)"
    }
}
Write-Host "完成：成功 $ok，失败 $fail"