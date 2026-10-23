# =============================================================================
# BiliNote 一键启动脚本（Windows / Docker Desktop / 单镜像版）
#
# 用法：
#   .\start-bilinote.ps1              # 启动，默认端口 3015
#   .\start-bilinote.ps1 -Port 8080   # 换端口
#   .\start-bilinote.ps1 -Recreate    # 删掉旧容器重建（数据不会丢）
#
# 数据全部落在本目录 docker-data\ 下：
#   data\       SQLite 数据库（含 LLM 供应商配置）+ 生成的笔记
#   config\     转写器运行时配置（transcriber.json）
#   static\     笔记里引用的视频截图
#   models\     whisper 模型缓存（避免重复下载）
#
# 说明：单镜像用 supervisord 启动，镜像内 [supervisord] 段硬编码了环境变量，
#       所以 docker run -e 对转写器/模型大小这类参数不生效。
#       要改转写引擎/模型，请在网页「设置 → 音频转写配置」里改（会写进
#       docker-data\config\transcriber.json，重启不丢）。
#
# 本脚本额外挂载了改过 HF_ENDPOINT 的 supervisord.conf：
#       hf-mirror.com 目前对 huggingface_hub 0.30 的 308 跳转缺 x-linked-size，
#       会导致模型下载失败，所以改成直连 huggingface.co（需要代理/Clash TUN 在跑）。
#
# 首次启动后打开 http://127.0.0.1:<Port>/ ，进「设置 → 模型供应商」录入
# 要用的大模型 API Key（不写在本脚本里，也不进镜像）。
# =============================================================================
param(
    [int]$Port = 3015,
    [switch]$Recreate
)

$ErrorActionPreference = 'Continue'
# 脚本在 deploy/ 里，项目根目录是它的上一级
$root = Split-Path -Parent $PSScriptRoot
$dataDir   = Join-Path $root 'docker-data\data'
$configDir = Join-Path $root 'docker-data\config'
$staticDir = Join-Path $root 'docker-data\static'
$modelsDir = Join-Path $root 'docker-data\models'
$vectorDir = Join-Path $root 'docker-data\vector_db'
$exportDir = Join-Path $root 'bilinote_output_docs'
$supConf   = Join-Path $PSScriptRoot 'supervisord.conf'
$image     = 'ghcr.io/jefferyhcool/bilinote:latest'
$name      = 'bilinote'

foreach ($d in @($dataDir, $configDir, $staticDir, $modelsDir, $vectorDir, $exportDir)) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

docker info 2>$null 1>$null
if ($LASTEXITCODE -ne 0) { throw 'Docker 引擎没在运行，请先启动 Docker Desktop。' }

# 优先用本地构建的镜像（含前端 zip 导出等修复），没有则回退官方镜像
docker image inspect 'bilinote-fixed:latest' *> $null
if ($LASTEXITCODE -eq 0) { $image = 'bilinote-fixed:latest' }

if ($Recreate) {
    docker rm -f $name *> $null
} elseif ((docker ps -a --format '{{.Names}}') -contains $name) {
    Write-Host "容器 $name 已存在，直接启动它（如需应用新配置请加 -Recreate）。"
    docker start $name | Out-Null
    Write-Host "已启动：http://127.0.0.1:$Port/"
    return
}

docker run -d --name $name --restart unless-stopped -p "${Port}:80" `
    --mount "type=bind,source=$dataDir,target=/app/backend/data" `
    --mount "type=bind,source=$configDir,target=/app/backend/config" `
    --mount "type=bind,source=$staticDir,target=/app/backend/static" `
    --mount "type=bind,source=$modelsDir,target=/app/backend/models" `
    --mount "type=bind,source=$vectorDir,target=/app/backend/vector_db" `
    --mount "type=bind,source=$exportDir,target=/app/backend/exports" `
    --mount "type=bind,source=$supConf,target=/etc/supervisor/conf.d/supervisord.conf" `
    --mount "type=bind,source=$root\nginx\standalone.conf,target=/etc/nginx/conf.d/default.conf" `
    --mount "type=bind,source=$root\backend\app\services\note.py,target=/app/backend/app/services/note.py" `
    --mount "type=bind,source=$root\backend\app\utils\note_helper.py,target=/app/backend/app/utils/note_helper.py" `
    --mount "type=bind,source=$root\backend\app\gpt\prompt_builder.py,target=/app/backend/app/gpt/prompt_builder.py" `
    --mount "type=bind,source=$root\backend\app\validators\video_url_validator.py,target=/app/backend/app/validators/video_url_validator.py" `
    --mount "type=bind,source=$root\backend\app\downloaders\douyin_downloader.py,target=/app/backend/app/downloaders/douyin_downloader.py" `
    --mount "type=bind,source=$root\backend\app\routers\note.py,target=/app/backend/app/routers/note.py" `
    --mount "type=bind,source=$root\backend\app\db\video_task_dao.py,target=/app/backend/app/db/video_task_dao.py" `
    $image

Write-Host ''
Write-Host "BiliNote 已启动：http://127.0.0.1:$Port/"
Write-Host "查看日志：docker logs -f $name"
Write-Host "后端详细日志：docker exec $name tail -f /var/log/supervisor/backend.log"
