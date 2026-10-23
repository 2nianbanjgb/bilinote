# 重新构建本地镜像 bilinote-fixed:latest（后端修复 + 前端 zip 导出）
#
#   .\构建镜像.ps1            # 拉最新上游镜像 + 重建前端 + 重建本地镜像
#   .\构建镜像.ps1 -NoPull    # 不拉上游，直接用本地已有的 ghcr 镜像
#
# 构建完运行：.\start-bilinote.ps1 -Recreate
param([switch]$NoPull)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root

if (-not $NoPull) {
    Write-Host '[1/4] 拉取上游最新镜像...'
    docker pull ghcr.io/jefferyhcool/bilinote:latest
} else {
    Write-Host '[1/4] 跳过拉取上游镜像'
}

Write-Host '[2/4] 构建前端（vite build）...'
docker build --target builder -f BillNote_frontend/Dockerfile -t bilinote-fe-builder .
if ($LASTEXITCODE -ne 0) { throw '前端构建失败' }

Write-Host '[3/4] 导出 dist...'
docker rm -f fe-tmp *> $null
docker create --name fe-tmp bilinote-fe-builder | Out-Null
Remove-Item "$root\frontend-dist" -Recurse -Force -ErrorAction SilentlyContinue
docker cp fe-tmp:/app/dist "$root\frontend-dist"
docker rm -f fe-tmp | Out-Null

Write-Host '[4/4] 构建 bilinote-fixed 镜像...'
docker build -f Dockerfile.local -t bilinote-fixed:latest .
if ($LASTEXITCODE -ne 0) { throw '镜像构建失败' }

Write-Host ''
Write-Host '完成。执行 .\start-bilinote.ps1 -Recreate 生效。'