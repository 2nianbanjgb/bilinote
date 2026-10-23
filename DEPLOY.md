# BiliNote 本地部署说明（D:\Project_OpenSource\bilibili_note）

## 0. 每天开机后怎么启动（日常只需这一步）

**双击 `启动BiliNote.bat`**，等黑窗口显示 `BiliNote is ready` 就会自动打开浏览器。

脚本会依次做三件事，全程 30 秒～2 分钟（取决于 Docker 启动速度）：

1. 发现 Docker Desktop 没运行就帮你拉起来（没装/起不来会提示）
2. 等 Docker 引擎就绪（最多等 4 分钟，超时会告诉你去看 Docker 的报错）
3. 启动 `bilinote` 容器，等网页能响应后自动打开 <http://127.0.0.1:3015/>

开机后**不需要**手动开 Docker Desktop、不需要开命令行。如果双击后浏览器没弹出来，
直接自己打开 <http://127.0.0.1:3015/> 也行。中途别关那个黑窗口。

想关掉服务：右下角鲸鱼图标 → Containers 里停掉 `bilinote`，或命令行 `docker stop bilinote`。

## 1. 现在就能用

- 访问地址：<http://127.0.0.1:3015/>
- 容器名：`bilinote`（Docker 单镜像，nginx + FastAPI 后端在同一容器里）
- 首次使用只差一步：**在网页里填你的大模型 API Key**
  1. 打开网页 → 左下角「设置」→「模型供应商」
  2. 选一个内置供应商（DeepSeek / Qwen / OpenAI / Claude / Gemini / Groq / Ollama）
     或点「新增」填任意 OpenAI 兼容接口（base_url + api_key + 模型名）
  3. 填 Key → 保存 → 在「模型」里选中要用的模型
  4. 回首页粘贴 B 站 / YouTube / 抖音 / 快手链接 → 生成笔记

> Key 保存在 `docker-data\data\bili_note.db`（SQLite），不进镜像、不进 git。

## 2. 目录结构

```
D:\Project_OpenSource\bilibili_note\
├─ backend\ BillNote_frontend\ ...   项目源码（git clone 的）
├─ supervisord.conf                  改过 HF_ENDPOINT 的容器启动配置
├─ 启动BiliNote.bat                    ★ 日常双击这个（自动开 Docker + 开容器 + 开浏览器）
├─ start-bilinote.ps1                底层启动脚本（首次创建容器 / 改端口 / 重建时用）
├─ docker-data\
│  ├─ data\      bili_note.db（供应商配置、笔记历史）+ note_results\ 生成的笔记
│  ├─ config\    transcriber.json（转写引擎 / whisper 模型大小）
│  ├─ static\    screenshots\ 笔记里引用的视频截图
│  └─ models\    whisper 模型缓存（base 已预下载，141MB）
└─ DEPLOY.md
```

常用命令：

```powershell
.\启动BiliNote.bat                   # 日常启动（等价于双击）
.\启动BiliNote.bat /silent           # 静默启动，不开浏览器
.\start-bilinote.ps1 -Recreate       # 重建容器（数据不丢）
.\start-bilinote.ps1 -Port 8080      # 换端口（同时要改启动BiliNote.bat 里的 PORT）
docker logs -f bilinote                                       # 容器日志
docker exec bilinote tail -f /var/log/supervisor/backend.log  # 后端详细日志
docker stop bilinote                                          # 停止服务
```

升级：

```powershell
docker pull ghcr.io/jefferyhcool/bilinote:latest
.\start-bilinote.ps1 -Recreate
```

## 3. 需要额外配置的 API（三类，只有第一类必填）

| 用途 | 是否必填 | 说明 |
|---|---|---|
| 大模型（写笔记 + 问答） | **必填** | DeepSeek / Qwen / OpenAI / Claude / Gemini / Groq / Ollama 或任意 OpenAI 兼容接口 |
| 语音转写 | 不必填 | 默认本地 `fast-whisper`，不需要 Key；换 Groq 才需要 Key |
| B 站 Cookie | 可选 | 抓 1080P/会员/登录可见视频时在「设置 → 下载配置」填 |

## 4. 免费 / 收费

**项目本身**

- 开源自托管：MIT 协议，**完全免费**，功能没有阉割、没有次数限制。
- BiliNote Pro 在线版（www.bilinote.app）：托管服务，目前内测免费；官方明确后续按视频时长计费
  + 订阅会员（长视频按时长精算），属于**付费服务**，与本机部署无关。
- 作者另有付费的「一对一搭建服务 / 企业咨询」，纯人工服务，不是软件收费。

**本机部署后每一环的钱**

| 环节 | 免费方案 | 收费方案 |
|---|---|---|
| 语音转写 | `fast-whisper`（本地 CPU/GPU 跑，已预下载 base）；必剪 `bcut`、快手 `kuaishou` 在线接口（无 Key，白嫖） | Groq（有免费额度，超了按量付费）；自己换更大 whisper 模型只花电费 |
| 视频下载 | yt-dlp 抓 B 站/YouTube/抖音/快手，免费 | 无 |
| 大模型写笔记 | Ollama 本地模型（如 qwen2.5:7b，0 成本，但笔记本上慢、质量一般）；各家新用户免费额度 | DeepSeek / Qwen / OpenAI / Claude / Gemini 按 token 计费。一条 30 分钟视频的转写文本约 1 万 token，DeepSeek 级别通常**几分钱一条** |
| 截图 / 跳转 / 导出 | 本地 FFmpeg 截图、Markdown/PDF/Word 导出，免费 | 无 |

结论：**软件免费，唯一持续成本是大模型 token**；用 Ollama 或新用户额度可以做到 0 元。

## 5. 已处理的坑（重装/换机器时注意）

1. **hf-mirror 下载模型失败**：hf-mirror 现在对 `huggingface_hub 0.30` 的 308 跳转缺
   `x-linked-size` 头，模型下载会报 `LocalEntryNotFoundError`。已把挂载的
   `supervisord.conf` 里 `HF_ENDPOINT` 改为 `https://huggingface.co`（依赖你的代理/Clash TUN）。
   如果你的代理关了，模型下载会失败 —— 打开代理再在「音频转写配置」里点下载即可。
2. **`docker run -e` 改不动转写配置**：单镜像用 supervisord 启动，`[supervisord]` 段把
   `WHISPER_MODEL_SIZE` 等硬编码了，`-e` 会被覆盖。改这些请走网页「设置 → 音频转写配置」，
   会写进 `docker-data\config\transcriber.json`。
3. **Docker Desktop 代理**：原来指向 `127.0.0.1:33210`（已失效），已改成你 Clash 的
   `127.0.0.1:7897`，所以能拉 ghcr.io 镜像。
4. **没有启用 GPU**：容器是 CPU 版，`fast-whisper base` 在你这台 4060 笔记本的 CPU 上跑
   30 分钟视频大约几分钟。想更快：网页里换 `bcut`（在线、免费）或 `tiny`；想更准：换 `small`。
5. **音频很长的视频**：转写和总结都在后台串行执行，前端每 3 秒轮询，别关页面就行（任务在服务端继续）。
6. **网络 / 代理：容器走不走 VPN，由 Docker 启动那一刻决定**
   现状：Docker Desktop 代理模式 = **System proxy**（跟随 Windows 系统代理）。
   - 系统代理关（Clash 没开）→ 容器**直连**：B 站、抖音、DeepSeek 都正常。
   - 系统代理开（Clash 运行时自动打开）→ 容器走代理：YouTube、Groq、HF 模型、docker pull 可用。
   - **关键规则：Docker 只在引擎启动时读一次系统代理**，之后改系统代理不会生效。
     所以顺序是「先开/关 Clash → 再启动 Docker」；Docker 已在跑就先托盘 Quit 再双击 `启动BiliNote.bat`。
   - 节点怎么换都无所谓：容器看到的始终是本地 `127.0.0.1:7897`，Clash 内部换节点对容器透明。

   报错 `SSL: UNEXPECTED_EOF_WHILE_READING` / yt-dlp `Unable to download webpage` 就是
   容器被指到了一个没有监听的代理上。验证：
   `docker exec bilinote python -c "import urllib.request;print(urllib.request.urlopen('http://www.baidu.com',timeout=10).status)"`
   → 报错就说明代理状态和 Docker 启动时不一致，重启 Docker 引擎即可。
   备选：如果你习惯长期开着 Clash，也可以把代理模式改回 **Manual / 127.0.0.1:7897**，
   这样不用管启动顺序，但 Clash 必须一直在线。
7. **历史会不会丢**：不会。生成历史存在**浏览器 IndexedDB**（`task-storage`），服务端另有
   `docker-data\data\bili_note.db` + `note_results\*.md` 副本。关机重启、容器重建都不影响；
   只有清浏览器数据、换浏览器/无痕模式会看不到前端历史（md 副本还在 note_results 里）。

8. **截图 / 时间戳跳转不生效（已修好，用 bind mount 覆盖源码）**：三个真 bug ——
   replace_content_markers 里的 UnboundLocalError 让链接替换整段异常被吞；B 站链接漏了
   `?`（生成 `...BVxxx&t=123` 打不开对应位置）；重试复用 task_id 时命中音频缓存，
   直接跳过视频下载导致没图可截。已修 `backend/app/utils/note_helper.py` 和
   `backend/app/services/note.py`，并在 `start-bilinote.ps1` 里挂载进容器，重建容器仍生效。
   注意：`data\note_results\<task_id>_markdown.md` 是**没做后处理的原始输出**（带 *Content-[mm:ss]*
   标记），后处理结果在 `<task_id>.json` 和网页里。
9. **临时音视频会自动清理（本仓库已修）**：上游的 `on_finish` 全被注释掉，媒体文件永不删除；
   现在 `NoteGenerator.generate` 在任务结束（成功或失败）时调用 `_cleanup_media_files` 删掉
   本次的 mp3/mp4，并校验音频缓存是否还在，不在了就自动重下。
   历史上遗留的旧文件仍在 `docker-data\data\data\`，可以手动清一次。
10. **B 站 Cookie 必须含 SESSDATA**：`document.cookie` 拿不到 HttpOnly 的 SESSDATA，
    要 DevTools → Application → Cookies → bilibili.com → 复制 SESSDATA，或装官方浏览器插件同步。
    没有 SESSDATA 就是游客身份：只有 360P/480P、拿不到 AI 字幕、也没有大会员画质。
11. **截图数量**：模型会给每个小节都打 `*Screenshot-[mm:ss]` 标记，一条 6 分钟视频能出
    几十张图。想控制就在「备注」里写「每节最多一张截图，总共不超过 10 张」。
12. **导出的 md 图片打不开**：md 里只有 `![](/static/screenshots/xxx.jpg)` 这种**网站根路径**，
    图片本体在 `docker-data\static\screenshots\`，导出 md 不会带图，本地编辑器解析不了。
    用 `整理笔记图片.ps1` 处理（三种模式）：
    `.\整理笔记图片.ps1 -MdPath "D:\笔记\xxx.md"`              # 图片复制到 xxx.assets\，改相对路径（离线可用）
    `.\整理笔记图片.ps1 -MdPath "D:\笔记\xxx.md" -Mode url`     # 改成 http://127.0.0.1:3015/static/...（需服务在跑）
    `.\整理笔记图片.ps1 -MdPath "D:\笔记\xxx.md" -Mode base64`  # 图片内嵌进 md，单文件但体积大
    也可以 `-TaskId <id>` 直接从服务端结果导出。默认不覆盖原文件，输出 `xxx.local.md`。
## 6. 本地相对上游改了什么（重启 / 重建 / 分享都看这一节）

| 文件 | 改了什么 | 生效方式 |
|---|---|---|
| `backend/app/services/note.py` | 需要截图/视频理解时不再复用音频缓存；任务结束自动清理临时音视频；缓存文件消失时重下 | bind mount 进容器 |
| `backend/app/utils/note_helper.py` | 修 UnboundLocalError（时间戳链接整段失效）；B 站链接补 `?t=`；吃掉标记尾部的 `*` | bind mount 进容器 |
| `backend/app/gpt/prompt_builder.py` | 追加固定规则：标题/小标题不编号 | bind mount 进容器 |
| `backend/app/routers/note.py` + `db/video_task_dao.py` | `/delete_task` 从空实现改成真删：结果文件、引用到的截图、临时媒体、向量索引、数据库记录 | bind mount 进容器 |
| `supervisord.conf` | `HF_ENDPOINT` 改直连 huggingface.co（hf-mirror 的 308 缺头） | bind mount 进容器 |
| `start-bilinote.ps1` | 挂载上面 6 个文件 + 4 个数据目录 | 每次建容器时执行 |
| `启动BiliNote.bat` | 双击启动：拉起 Docker → 建/启动容器 → 开浏览器 | 手动运行 |
| `整理笔记图片.ps1` | 把 md 里的 `/static/screenshots/...` 变成本地可看 | 手动运行 |
| `Dockerfile.local` | 把上面 6 个文件固化进镜像 | `docker build -f Dockerfile.local -t bilinote-fixed:latest .` |

**重启电脑 / `docker rm` 重建容器 / `-Recreate` 后都仍然生效**，因为文件在 D 盘仓库里，启动脚本每次都重新挂进去。

但注意：如果你**绕过启动脚本**直接 `docker run ghcr.io/jefferyhcool/bilinote:latest`，或者按上游 README 用
`docker-compose up`，这些修复**不会生效**（那两个是原始代码）。

### 分享给别人

- **最省事**：让对方 clone 后执行
  `docker build -f Dockerfile.local -t bilinote-fixed:latest .`
  然后用这个镜像跑，修复已经固化，不依赖源码挂载。
- 或者让对方用自己的路径跑 `start-bilinote.ps1`（脚本里路径是 `D:\Project_OpenSource\bilibili_note`，要改）。
- **不会跟着仓库走的东西**：`docker-data\`（数据库、笔记、截图、whisper 模型、Cookie、API Key）、
  Docker Desktop 的代理设置、系统代理开关。这些每个人自己配。

上游剩下的问题：设置里的「Prompt」页仍是空占位（提示词规则目前写死在 `prompt_builder.py`）；
另外前端删除是「先删浏览器记录再调接口」，接口失败时本地历史已消失、文件可能残留。
## 7. 第二批改动（2026-10-23）

| 改动 | 说明 |
|---|---|
| 导出 zip | 前端重新构建：有截图时「下载」直接给 `<标题>.zip`（内含 `<标题>.md` + `<标题>/` 图片目录，路径已改相对）。无截图仍下 md |
| 时间戳独立成行 | `## 标题 [原片 @ 01:23](...)` → `## 标题` 换行 `[原片 @ 01:23](...)` |
| 孤儿截图防护 | 同一 task 重新生成前，先删上一版 json 引用的截图；任务结束清空 `data\grid_output`、`data\output_frames` |
| 清理残留 | 新增 `清理残留.ps1`：默认 dry-run 统计孤儿截图/抽帧/媒体/失败任务，`-Apply` 才删 |
| 向量库持久化 | `docker-data\vector_db` 挂载到容器 `/app/backend/vector_db`，重建不丢 AI 问答索引 |
| 本地镜像 | 新增 `构建镜像.ps1`（拉上游 → vite build → 导出 dist → 打包 `bilinote-fixed`）；`start-bilinote.ps1` 自动优先用本地镜像 |

当前状态：`docker-data` 已从约 175MB 清到 141MB（删了 183 张孤儿截图 + 87 个抽帧文件，共 30.75MB）。