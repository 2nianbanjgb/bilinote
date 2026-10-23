# 上游部署方式（备选，不是本项目日常用的那套）

这里放的是上游仓库自带的 docker-compose / 一体化 Dockerfile，日常部署**不需要**它们。
本项目用的是根目录的 `Dockerfile.local` + `deploy/start-bilinote.ps1`（单镜像 + 绑定挂载）。

## 想用这套时

所有命令都在**仓库根目录**执行（构建 context 需要根目录）：

```powershell
# 1) 准备环境变量（从根目录的示例文件复制）
Copy-Item .env.example .env

# 2) compose 方式（backend + frontend + nginx 三个容器）
docker compose --env-file .env -f deploy/upstream/docker-compose.yml up --build -d

# GPU 版本（需要 NVIDIA 驱动 + Container Toolkit）
docker compose --env-file .env -f deploy/upstream/docker-compose.gpu.yml up --build -d

# 3) 或者用一体化镜像（单容器，端口 80）
docker build -f deploy/upstream/Dockerfile.complete -t bilinote-aio .
docker run -d -p 8080:80 --name bilinote-aio bilinote-aio
```

## 注意

- compose 文件里的 `context` 已改成 `../..`，所以**必须在仓库根目录**跑，别 cd 进来
- 三个容器共用项目根目录的 `.env`（`--env-file .env` 指定插值文件，`env_file` 里是容器环境变量）
- 这套部署**不会**自动带上本仓库修过的 bug 修复（那些修复挂在 `Dockerfile.local` 和 `deploy/` 的脚本里）
