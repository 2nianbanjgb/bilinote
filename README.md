# BiliNote 本地版（Windows + Docker）

把 B 站 / YouTube / 抖音 / 快手的视频链接变成结构化 Markdown 笔记：自动抓字幕或转写、用大模型总结、可选插入原片截图和时间戳跳转。

本仓库基于 [JefferyHcool/BiliNote](https://github.com/JefferyHcool/BiliNote)（MIT），**额外修了几个上游 bug**（见「相对上游的改动」），并把部署方式固定为 Windows + Docker Desktop 单镜像。上游原始 README 保留在 [README.upstream.md](README.upstream.md)。

- 访问地址：<http://127.0.0.1:3015/>
- 数据目录：`docker-data\`（就在本仓库里，删容器不丢）
- 不需要装 Python / Node / ffmpeg，全部在容器里

---

## 1. 第一次使用（3 步）

1. 装好 **Docker Desktop**（本项目用 4.38 验证过），启动到鲸鱼图标常驻
2. 双击 **`启动BiliNote.bat`** —— 它会自动拉起 Docker、启动容器、等网页就绪、打开浏览器
3. 浏览器打开 <http://127.0.0.1:3015/>，按下一节配好模型就能用

> 黑窗口显示 `BiliNote is ready` 就可以关掉它了。中途别关，它要等 Docker 起来。

不想用启动脚本也可以：

```powershell
.\start-bilinote.ps1              # 启动；已存在则启动旧容器
.\start-bilinote.ps1 -Recreate    # 重建容器（数据不丢）
.\start-bilinote.ps1 -Port 8080   # 换端口
```

---

## 2. 首次配置（按这个顺序，别跳）

全部在网页左下角 **设置** 里完成，配置都存进 `docker-data\data\bili_note.db`，重启不丢。

### 第 1 步：配大模型（必做）

「设置 → 模型供应商」→ **DeepSeek**：

- `API Key`：填你的 `sk-...`
- `模型名`：填 **`deepseek-flash`**（DeepSeek V4.1 Flash，1M 上下文，支持图片）
  想要纯推理可以用 `deepseek-v4-pro`
- 保存后，首页的「模型」下拉里选中它

> 旧模型名 `deepseek-chat` / `deepseek-reasoner` 官方已下线（旧名会被静默转发到 V4.1，但别依赖）。
> 也支持 OpenAI / Qwen / Gemini / Claude / Ollama，或「新增」任意 OpenAI 兼容接口。

### 第 2 步：配 B 站 Cookie（想高清 / 大会员必做）

「设置 → 下载配置」→ **Bilibili** → 粘贴 Cookie 字符串。

- 关键在于 **SESSDATA**：它是 HttpOnly，`document.cookie` 抓不到，
  要从 DevTools → **Application → Cookies → bilibili.com** 里复制
- 或者装 **Cookie-Editor** 插件 → Export → Header String，一次拿全（含 HttpOnly）
- 大会员画质（1080P+ / 4K）、B 站 AI 字幕，全靠这个登录态

抖音同理：「下载配置 → 抖音」，需要 `ttwid`、`msToken` 等；不带 Cookie 经常直接失败。

### 第 3 步：选转写引擎（一般不用动）

「设置 → 音频转写配置」：

| 引擎 | 说明 |
|---|---|
| **Faster Whisper（本地）** | 默认。`base` 模型已预下载，CPU 跑 6 分钟视频约 1 分钟 |
| 必剪 / 快手（在线） | 免费、无需 Key，速度最快，依赖第三方接口稳定性 |
| Groq（在线） | 要 Groq API Key，有免费额度 |

有字幕的视频（尤其配了 Cookie 的 B 站）会优先用字幕，根本不走转写。

### 第 4 步：代理（按需，理解这条规则能省很多事）

Docker 的代理模式是 **System proxy**，意思是「容器跟随 Windows 系统代理」，而 Docker **只在引擎启动时读一次**：

- **不挂 VPN** → 先确认 Clash 是关的 → 双击启动脚本 → 容器**直连**，B 站/抖音/DeepSeek 全通
- **要下 YouTube / 用 Groq / 拉镜像** → 先开 Clash → 如果 Docker 在跑，托盘 Quit 再双击脚本

节点随便换都不影响（容器看到的始终是本地固定端口）。详见「常见问题 · SSL EOF」。

---

## 3. 日常使用流程

1. 首页粘贴视频链接（`BV...`、`av...`、`b23.tv` 短链都行）
2. 选 **模型**、**笔记风格**（详细/教程/学术/会议纪要…）
3. 「笔记格式」按需勾选：
   - **目录**：生成 `## 目录`
   - **原片跳转**：在标题后插入 `[原片 @ 03:12](...?t=192)`，点了直接定位
   - **原片截图**：在正文插入关键帧图片
   - **AI 总结**：结尾加一段摘要
4. 「备注」可写额外要求，比如 `每节最多一张截图，总共不超过 10 张`
5. 点「生成笔记」，等步骤条走完（下载 → 转写 → 总结 → 保存）
6. 右侧预览顶部有 **复制** 和 **下载**，下载得到 `<视频标题>.md`

### 关于「原片截图」的一个坑（上游设计）

截图复选框只有在「视频理解 → 启用」之后才能勾。因为两者共用「下载原片 → 抽帧」的链路，UI 把它们绑在一起了。

- 只想要文字：**别开**视频理解，省下载也省 token
- 想要截图：勾「视频理解」→ 再勾「原片截图」；模型必须支持图片（`deepseek-flash` 支持，`deepseek-v4-pro` 不支持）

### 导出后的图片怎么办

md 里写的是 `![](/static/screenshots/xxx.jpg)`，这只是**网站路径**。图片本体在 `docker-data\static\screenshots\`，本地编辑器解析不了。用附带脚本处理：

```powershell
.\整理笔记图片.ps1 -MdPath "D:\笔记\xxx.md"              # 图片复制到 xxx.assets\，改相对路径（离线可用）
.\整理笔记图片.ps1 -MdPath "D:\笔记\xxx.md" -Mode url    # 改成 http://127.0.0.1:3015/...（需服务在跑）
.\整理笔记图片.ps1 -MdPath "D:\笔记\xxx.md" -Mode base64 # 图片内嵌进 md，单文件但体积大
```

---

## 4. 数据都在哪

```
D:\Project_OpenSource\bilibili_note\
├─ 启动BiliNote.bat          ★ 日常双击
├─ start-bilinote.ps1        底层启动/重建脚本
├─ 整理笔记图片.ps1           导出 md 的图片整理
├─ supervisord.conf          容器内启动配置（已改 HF_ENDPOINT）
├─ Dockerfile.local          把修复固化进镜像（分享用）
├─ docker-data\
│  ├─ data\
│  │  ├─ bili_note.db         供应商/模型/任务映射（含明文 API Key）
│  │  ├─ note_results\        每篇笔记的 md / json / 转写缓存
│  │  └─ data\                临时 mp3/mp4（任务结束会自动删）
│  ├─ config\                 转写器、代理、各平台 Cookie
│  ├─ static\screenshots\     截图（会累积）
│  └─ models\                 whisper 模型（base 已预下载，141MB）
└─ DEPLOY.md                 运维细节与踩坑记录
```

- **你在网页看到的笔记正文来自浏览器 IndexedDB**，服务端另存了一份快照（`note_results`）
- **网页点删除现在会真删**：结果文件 + 截图 + 临时媒体 + 向量索引 + 数据库记录（上游是空实现，本仓库已修）
- **临时音视频在任务结束时自动清理**（上游从不清理）
- 截图不会自动清，嫌多就手动删 `docker-data\static\screenshots\`

---

## 5. 常见问题

| 现象 | 原因 / 解决 |
|---|---|
| `SSL: UNEXPECTED_EOF_WHILE_READING` | 容器被指到死代理。开 Clash 重开 Docker，或关掉 Clash 后重启 Docker（详见第 2 节第 4 步） |
| 只有 360P / 没有 AI 字幕 | Cookie 缺 `SESSDATA`（或是游客）。按第 2 节第 2 步补上 |
| 笔记里没有截图 | 没开「视频理解」；或走了旧音频缓存（本仓库已修，仍建议重新生成一次） |
| 时间戳点了回开头 | 旧版本 bug（链接少了 `?`），本仓库已修 |
| 模型报 404 / 不存在 | `deepseek-chat` 已下线，用 `deepseek-flash` |
| 网页打不开 | Docker 没起来，先双击 `启动BiliNote.bat`；端口冲突用 `-Port` |
| 生成很慢 | 长视频先用「必剪」在线转写，或把 whisper 切到 `tiny` |
| 磁盘涨得快 | 清 `static\screenshots\` 和 `data\data\`；whisper 模型 141MB 可留 |

---

## 6. 相对上游的改动

| 文件 | 改动 |
|---|---|
| `backend/app/services/note.py` | 需要截图时不再复用音频缓存（否则永不下视频）；任务结束清理临时音视频；缓存文件消失时自动重下 |
| `backend/app/utils/note_helper.py` | 修 `UnboundLocalError`（时间戳链接整段失效）；B 站链接补 `?t=`；清掉标记尾部的 `*` |
| `backend/app/routers/note.py` + `db/video_task_dao.py` | `/delete_task` 从空实现改成真正删除文件/截图/媒体/向量/数据库记录 |
| `backend/app/gpt/prompt_builder.py` | 固定规则：标题/小标题不编号（交给 Markdown 编辑器编号） |
| `supervisord.conf` | `HF_ENDPOINT` 直连 huggingface.co（hf-mirror 的 308 缺 `x-linked-size`） |
| `start-bilinote.ps1` / `启动BiliNote.bat` | 一键启动 + 把上面几个文件挂载进容器 |
| `整理笔记图片.ps1` | md 图片本地化 / 转 URL / 内嵌 base64 |
| `Dockerfile.local` | 把上述修复固化进镜像 |

这些文件通过 `start-bilinote.ps1` 的 bind mount 注入容器，**重启电脑、重建容器都保留**。
唯一例外：绕过启动脚本直接 `docker run` 官方镜像，就是原版代码。

---

## 7. 升级 / 备份 / 分享

**升级**（保留数据与修复）：

```powershell
docker pull ghcr.io/jefferyhcool/bilinote:latest
.\start-bilinote.ps1 -Recreate
```

升级后如果上游大改了被挂载的那几个文件导致不兼容，删掉 `start-bilinote.ps1` 里对应的 `--mount` 行再试。

**备份**：复制 `docker-data\data\`（数据库 + 笔记）即可；`models\` 141MB 不必备份，可重下。

**分享给别人**（修复固化，不依赖源码挂载）：

```powershell
docker build -f Dockerfile.local -t bilinote-fixed:latest .
docker run -d --name bilinote -p 3015:80 --restart unless-stopped `
  -v ${PWD}\docker-data\data:/app/backend/data `
  -v ${PWD}\docker-data\config:/app/backend/config `
  -v ${PWD}\docker-data\static:/app/backend/static `
  -v ${PWD}\docker-data\models:/app/backend/models `
  bilinote-fixed:latest
```

别人需要自己配 API Key、Cookie、代理设置——这些不在仓库里。

---

## 8. 安全提醒

- `docker-data\data\bili_note.db` 里 **API Key 是明文**，`config\downloader.json` 里 **Cookie 是明文**
- 别把这两个文件、或整个 `docker-data\` 传给任何人 / 传到公开仓库
- Cookie 等价账号登录态，泄露等于把账号交出去；B 站 Cookie 有效期通常几个月，失效后重新复制

---

## 9. 许可

上游 MIT。本仓库的改动同样以 MIT 发布。上游原始说明见 [README.upstream.md](README.upstream.md)，详细运维记录见 [DEPLOY.md](DEPLOY.md)。
