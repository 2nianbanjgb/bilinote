#!/usr/bin/env node
/**
 * fix_math_delimiters.mjs —— 统一 Markdown 中的 LaTeX 公式定界符
 *
 * 目标格式（大多数 Markdown 编辑器 / Typora / Obsidian / VS Code 预览都认）：
 *   行间公式（display）：$$ ... $$
 *   行内公式（inline） ：$ ... $
 *
 * 能自动识别并转换：
 *   \( ... \)   →  $ ... $        （行内）
 *   \[ ... \]   →  $$ ... $$      （独占多行时转成块级；行中间的保持行内 $$..$$）
 *   $ ... $     →  保持不动（已经符合要求）
 *   $$ ... $$   →  保持不动（已经符合要求）
 *
 * 不会误伤：
 *   - 围栏代码块 ``` / ~~~ 里的内容
 *   - 行内代码 `...` 里的内容
 *   - 转义写法 \$、\`、\\（例如 "[2pt]" 前面的双反斜杠、\$5 这类金额）
 *   - 公式内部的 LaTeX 命令（\left( ）\right)、\frac、\leftarrow …）原样保留
 *   - 空定界符 \(\) 原样保留
 *
 * 行为特性：幂等（重复运行不会二次改动）、保留原文件的 BOM 与换行符（CRLF/LF）、
 *           默认写入前生成 .bak 备份。
 *
 * 用法（只依赖 Node.js ≥ 14，无需 npm 安装任何东西）：
 *   node fix_math_delimiters.mjs                 # 处理当前目录下所有 .md（就地写入，自动 .bak 备份）
 *   node fix_math_delimiters.mjs 笔记.md          # 处理指定文件
 *   node fix_math_delimiters.mjs a.md b.md       # 处理多个文件
 *   node fix_math_delimiters.mjs -n .            # 只预览会改什么，不写盘
 *   node fix_math_delimiters.mjs -r docs/        # 递归处理子目录
 *   node fix_math_delimiters.mjs --check .       # CI 用：有需要修正的文件时退出码为 1
 *   node fix_math_delimiters.mjs --self-test     # 跑内置自测
 *
 * 选项：
 *   -n, --dry-run     只预览，不写入文件
 *   -r, --recursive   递归处理子目录
 *       --no-backup   不生成 .bak 备份
 *   -v, --verbose     打印每一处转换的前后对比
 *   -q, --quiet       只打印需要修正的文件
 *       --check       配合 CI：存在待修正文件时退出码 1
 *       --self-test   运行内置用例自检
 *   -h, --help        显示帮助
 */

import fs from 'node:fs';
import path from 'node:path';

const NL = '\n';
const MD_EXT = /\.(md|markdown|mdx)$/i;

/* ============================== 小工具 ============================== */

function escRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function buildLineStarts(text) {
  const starts = [0];
  for (let k = 0; k < text.length; k += 1) {
    if (text[k] === NL) starts.push(k + 1);
  }
  return starts;
}

/** 由绝对字符偏移求 1 起始的行号（二分查找） */
function lineOf(starts, abs) {
  let lo = 0;
  let hi = starts.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (starts[mid] <= abs) lo = mid;
    else hi = mid - 1;
  }
  return lo + 1;
}

/* ========================= 围栏代码块切分 ========================= */

/**
 * 把源文件切成「围栏代码块」与「普通文本」两类片段，两类片段首尾相接、
 * 完整覆盖原文，因此每一段都能用 src.slice 精确取出，不会破坏换行。
 */
function splitFences(src) {
  const lines = src.split(NL);
  const off = new Array(lines.length + 1);
  off[0] = 0;
  for (let k = 0; k < lines.length; k += 1) {
    off[k + 1] = Math.min(off[k] + lines[k].length + 1, src.length);
  }

  const segs = [];
  let fence = null; // { ch, len, startLine }
  let textStart = 0;

  const pushText = (endLine) => {
    if (endLine > textStart) {
      segs.push({ type: 'text', text: src.slice(off[textStart], off[endLine]) });
    }
  };

  for (let k = 0; k < lines.length; k += 1) {
    const line = lines[k];

    if (fence) {
      const close = new RegExp(`^[ \\t]*${escRe(fence.ch)}{${fence.len},}[ \\t]*$`);
      if (close.test(line)) {
        segs.push({ type: 'fence', text: src.slice(off[fence.startLine], off[k + 1]) });
        fence = null;
        textStart = k + 1;
      }
      continue;
    }

    const open = /^[ \t]*(`{3,}|~{3,})/.exec(line);
    if (open) {
      pushText(k);
      fence = { ch: open[1][0], len: open[1].length, startLine: k };
    }
  }

  if (fence) {
    // 未闭合的围栏：按“剩余全文都是代码”处理，绝不改写
    segs.push({ type: 'fence', text: src.slice(off[fence.startLine], src.length) });
    textStart = lines.length;
  }

  pushText(lines.length);
  return segs;
}

/* ============================ 定界符查找 ============================ */

/**
 * 查找 \) 或 \]（closer 为 ')' 或 ']'），返回反斜杠所在下标。
 * 会跳过 \\ 之类的转义对；一旦碰到空行（段落边界）就放弃，
 * 避免一个未闭合的定界符把后面整篇正文都吞进公式里。
 */
function findClosing(text, from, closer) {
  let j = from;
  while (j < text.length) {
    if (text[j] === '\\') {
      if (text[j + 1] === closer) return j;
      j += 2;
      continue;
    }
    if (text[j] === NL) {
      let k = j + 1;
      while (k < text.length && (text[k] === ' ' || text[k] === '\t' || text[k] === '\r')) k += 1;
      if (k >= text.length || text[k] === NL) return -1; // 空行 = 段落结束
      j = k;
      continue;
    }
    j += 1;
  }
  return -1;
}

/** 查找行内 $ 的结束 $（只在本行内找；找不到视为普通美元符号） */
function findInlineDollarEnd(text, from) {
  let j = from;
  while (j < text.length) {
    const c = text[j];
    if (c === NL) return -1;
    if (c === '\\') {
      j += 2;
      continue;
    }
    if (c === '$') return j;
    j += 1;
  }
  return -1;
}

/** 查找块级 $$ 的结束 $$ */
function findBlockDollarEnd(text, from) {
  let j = from;
  while (j < text.length - 1) {
    if (text[j] === '\\') {
      j += 2;
      continue;
    }
    if (text[j] === '$' && text[j + 1] === '$') return j;
    j += 1;
  }
  return -1;
}

/** 查找等长反引号组成的行内代码结束位置；代码段不跨空行 */
function findCodeSpanEnd(text, from, len) {
  let j = from;
  while (j < text.length) {
    if (text[j] === '`') {
      let m = 0;
      while (text[j + m] === '`') m += 1;
      if (m === len) return j;
      j += m;
      continue;
    }
    if (text[j] === NL && text[j + 1] === NL) return -1;
    j += 1;
  }
  return -1;
}

/* ============================== 核心扫描 ============================== */

function scanText(text, startAtLineStart, ctx) {
  let out = '';
  let i = 0;
  let last = 0; // 尚未输出的原文起点
  const n = text.length;

  const lineStartIndex = (k) => {
    let s = k;
    while (s > 0 && text[s - 1] !== NL) s -= 1;
    return s;
  };

  while (i < n) {
    const ch = text[i];

    /* ---------- 反斜杠：转义 or 数学定界符 ---------- */
    if (ch === '\\') {
      const nx = text[i + 1] ?? '';

      // 转义字符：原样跳过
      if (nx === '\\' || nx === '$' || nx === '`') {
        i += 2;
        continue;
      }

      // \( ... \)  →  $ ... $
      if (nx === '(') {
        const end = findClosing(text, i + 2, ')');
        if (end === -1) {
          ctx.warn(`第 ${ctx.lineOf(i)} 行：未闭合的 \\(，已原样保留`);
          i += 2;
          continue;
        }
        const raw = text.slice(i + 2, end);
        const body = raw.trim();

        if (!body) {
          // 空定界符，保持原样
          i = end + 2;
          continue;
        }

        if (raw.includes(NL)) {
          // 多行的行内公式：多数编辑器渲染不了，升级为块级公式，
          // 必要时补换行，避免 $$ 和正文挤在同一行
          ctx.stats.multilineInline += 1;
          const before = text.slice(i, end + 2);

          const lsI = lineStartIndex(i);
          const atLineStartI = (lsI > 0 || startAtLineStart) && /^[ \t]*$/.test(text.slice(lsI, i));
          const nlI = text.indexOf(NL, end + 2);
          const tailI = text.slice(end + 2, nlI === -1 ? n : nlI);

          let repl = `$$${NL}${body}${NL}$$`;
          if (!atLineStartI) repl = NL + repl;
          if (!/^[ \t]*$/.test(tailI)) repl += NL;

          const chunk = text.slice(last, i);
          out += atLineStartI ? chunk : chunk.replace(/[ \t]+$/, '');
          out += repl;
          ctx.note(before, repl, '多行行内 → 块级');
          i = end + 2;
          last = i;
          continue;
        }

        const before = text.slice(i, end + 2);
        const repl = `$${body}$`;
        out += text.slice(last, i) + repl;
        ctx.stats.inline += 1;
        ctx.note(before, repl, '行内公式');
        i = end + 2;
        last = i;
        continue;
      }

      // \[ ... \]  →  $$ ... $$
      if (nx === '[') {
        const end = findClosing(text, i + 2, ']');
        if (end === -1) {
          ctx.warn(`第 ${ctx.lineOf(i)} 行：未闭合的 \\[，已原样保留`);
          i += 2;
          continue;
        }
        const raw = text.slice(i + 2, end);
        const body = raw.trim();

        if (!body) {
          i = end + 2;
          continue;
        }

        const ls = lineStartIndex(i);
        const prefix = text.slice(ls, i);
        const atLineStart = (ls > 0 || startAtLineStart) && /^[ \t]*$/.test(prefix);
        const nlOpen = text.indexOf(NL, i);
        const openTail = text.slice(i + 2, nlOpen === -1 ? n : nlOpen);
        const nlClose = text.indexOf(NL, end + 2);
        const closeTail = text.slice(end + 2, nlClose === -1 ? n : nlClose);
        const aloneOnLines = atLineStart && /^[ \t]*$/.test(openTail) && /^[ \t]*$/.test(closeTail);

        if (aloneOnLines) {
          // 独占整行：转成标准块级公式，保留原来的缩进
          const before = text.slice(ls, nlClose === -1 ? n : nlClose);
          const repl = `${prefix}$$${NL}${body}${NL}${prefix}$$`;
          out += text.slice(last, ls) + repl;
          ctx.stats.block += 1;
          ctx.note(before, repl, '块级公式');
          let j = end + 2;
          while (j < n && (text[j] === ' ' || text[j] === '\t')) j += 1; // 吃掉行尾空白
          i = j;
          last = i;
          continue;
        }

        // 夹在行中间的 \[..\]：改成行内 $$..$$，不打断段落
        const before = text.slice(i, end + 2);
        const repl = `$$${body}$$`;
        out += text.slice(last, i) + repl;
        ctx.stats.block += 1;
        ctx.note(before, repl, '行中 \\[..\\] → $$..$$');
        ctx.warn(`第 ${ctx.lineOf(i)} 行：\\[..\\] 出现在行中间，已改为行内 $$..$$`);
        i = end + 2;
        last = i;
        continue;
      }

      // 其他 \xxx 命令，原样保留
      i += 1;
      continue;
    }

    /* ---------- 行内代码 `...`：原样保留 ---------- */
    if (ch === '`') {
      let len = 0;
      while (text[i + len] === '`') len += 1;
      const end = findCodeSpanEnd(text, i + len, len);
      if (end === -1) {
        i += len;
        continue;
      }
      ctx.stats.codeSpans += 1;
      i = end + len;
      continue;
    }

    /* ---------- 已符合要求的 $ / $$：原样保留 ---------- */
    if (ch === '$') {
      if (text[i + 1] === '$') {
        const end = findBlockDollarEnd(text, i + 2);
        if (end === -1) {
          ctx.warn(`第 ${ctx.lineOf(i)} 行：未闭合的 $$，已原样保留`);
          i += 2;
          continue;
        }
        ctx.stats.existingBlock += 1;
        i = end + 2;
        continue;
      }

      const end = findInlineDollarEnd(text, i + 1);
      if (end === -1) {
        i += 1; // 普通的美元符号
        continue;
      }
      ctx.stats.existingInline += 1;
      i = end + 1;
      continue;
    }

    i += 1;
  }

  out += text.slice(last, n);
  return out;
}

/* ============================== 对外转换 ============================== */

export function transform(src) {
  const ctx = {
    stats: {
      block: 0,
      inline: 0,
      multilineInline: 0,
      existingBlock: 0,
      existingInline: 0,
      codeSpans: 0,
    },
    warnings: [],
    samples: [],
    lineStarts: buildLineStarts(src),
    offsetBase: 0,
    lineOf(pos) {
      return lineOf(this.lineStarts, this.offsetBase + pos);
    },
    warn(msg) {
      if (this.warnings.length < 30) this.warnings.push(msg);
    },
    note(before, after, kind) {
      if (this.samples.length < 4) this.samples.push({ before, after, kind });
    },
  };

  let out = '';
  let base = 0;
  for (const seg of splitFences(src)) {
    if (seg.type === 'fence') {
      out += seg.text;
    } else {
      ctx.offsetBase = base;
      const startsAtLineStart = out.length === 0 || out.endsWith(NL);
      out += scanText(seg.text, startsAtLineStart, ctx);
    }
    base += seg.text.length;
  }

  return { text: out, stats: ctx.stats, warnings: ctx.warnings, samples: ctx.samples };
}

/* ============================== 文件处理 ============================== */

function processFile(file, opts) {
  const raw = fs.readFileSync(file);
  let text = raw.toString('utf8');

  const bom = text.charCodeAt(0) === 0xfeff;
  if (bom) text = text.slice(1);

  const crlf = text.includes('\r\n');
  const work = crlf ? text.replace(/\r\n/g, NL) : text;

  const res = transform(work);
  const changed = res.text !== work;

  if (changed && !opts.dryRun) {
    if (opts.backup) fs.copyFileSync(file, `${file}.bak`);

    let finalText = res.text;
    if (crlf) finalText = finalText.replace(/\n/g, '\r\n');
    if (bom) finalText = `\ufeff${finalText}`;
    fs.writeFileSync(file, finalText, 'utf8');
  }

  return { file, changed, stats: res.stats, warnings: res.warnings, samples: res.samples };
}

function fmtStats(s) {
  const parts = [];
  if (s.block) parts.push(`块级 ${s.block} 处`);
  if (s.inline) parts.push(`行内 ${s.inline} 处`);
  if (s.multilineInline) parts.push(`多行行内→块级 ${s.multilineInline} 处`);
  return parts.join('，') || '0 处';
}

function preview(s) {
  const one = String(s).replace(/\s*\n\s*/g, ' ⏎ ');
  return one.length > 88 ? `${one.slice(0, 88)}…` : one;
}

/* ============================== 文件收集 ============================== */

function* walk(dir, recursive) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    if (e.name.startsWith('.')) continue;
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (recursive) yield* walk(full, true);
    } else if (e.isFile() && MD_EXT.test(e.name) && !e.name.endsWith('.bak')) {
      yield full;
    }
  }
}

function collectFiles(targets, recursive) {
  const out = [];
  for (const t of targets) {
    const abs = path.resolve(t);
    let st;
    try {
      st = fs.statSync(abs);
    } catch {
      console.error(`跳过不存在的路径：${t}`);
      continue;
    }
    if (st.isFile()) {
      out.push(abs);
    } else if (st.isDirectory()) {
      for (const f of walk(abs, recursive)) out.push(f);
    }
  }
  return [...new Set(out)].sort();
}

/* ============================== 命令行 ============================== */

function parseArgs(argv) {
  const opts = {
    targets: [],
    dryRun: false,
    recursive: false,
    backup: true,
    verbose: false,
    quiet: false,
    check: false,
    selfTest: false,
    help: false,
  };

  for (const a of argv) {
    if (a === '-h' || a === '--help') opts.help = true;
    else if (a === '--self-test') opts.selfTest = true;
    else if (a === '-n' || a === '--dry-run') opts.dryRun = true;
    else if (a === '-r' || a === '--recursive') opts.recursive = true;
    else if (a === '--no-backup') opts.backup = false;
    else if (a === '-v' || a === '--verbose') opts.verbose = true;
    else if (a === '-q' || a === '--quiet') opts.quiet = true;
    else if (a === '--check') opts.check = true;
    else if (a.startsWith('-')) {
      console.error(`未知选项：${a}`);
      opts.help = true;
    } else opts.targets.push(a);
  }

  if (!opts.targets.length) opts.targets.push('.');
  return opts;
}

function printHelp() {
  console.log(`用法：node fix_math_delimiters.mjs [选项] [文件或目录...]

把 Markdown 里的 LaTeX 公式定界符统一为：
  行间公式  $$ ... $$
  行内公式  $ ... $

转换规则：
  \\( ... \\)   →  $ ... $
  \\[ ... \\]   →  $$ ... $$（独占多行时为块级；行中间则为行内 $$..$$）
  $ / $$ 已符合要求，保持不动
代码块、行内代码、转义符 \\$ \\\` \\\\ 不会被改动。

选项：
  -n, --dry-run     只预览，不写入文件
  -r, --recursive   递归处理子目录
      --no-backup   不生成 .bak 备份（默认生成）
  -v, --verbose     打印每一处转换的前后对比
  -q, --quiet       只打印需要修正的文件
      --check       存在待修正文件时退出码为 1（适合 CI）
      --self-test   运行内置用例自检
  -h, --help        显示本帮助

示例：
  node fix_math_delimiters.mjs              # 当前目录所有 .md
  node fix_math_delimiters.mjs -n "笔记.md"  # 先看看会改什么
  node fix_math_delimiters.mjs -r ./docs     # 递归处理
`);
}

/* ============================== 自测 ============================== */

function runSelfTest() {
  const cases = [
    { name: '行内 \\(..\\)', input: '文本 \\(a+b\\) 结束', expect: '文本 $a+b$ 结束' },
    {
      name: '块级 \\[..\\]',
      input: '前文\n\\[\n a = b \n\\]\n后文',
      expect: '前文\n$$\na = b\n$$\n后文',
    },
    { name: '已合规不动', input: '行内 $x$ 与 $$y$$', expect: '行内 $x$ 与 $$y$$' },
    { name: '代码块不动', input: '```\n\\(a\\) \\(b\\)\n```', expect: '```\n\\(a\\) \\(b\\)\n```' },
    { name: '行内代码不动', input: '写作 `\\(x\\)` 即可', expect: '写作 `\\(x\\)` 即可' },
    { name: '转义美元不动', input: '价格 \\$5', expect: '价格 \\$5' },
    { name: 'LaTeX 命令不误伤', input: '公式 \\(\\left( x \\right)\\)', expect: '公式 $\\left( x \\right)$' },
    { name: '空定界符原样', input: '\\(\\)', expect: '\\(\\)' },
    { name: '双反斜杠不误判', input: '换行 \\\\[2pt]', expect: '换行 \\\\[2pt]' },
    { name: '行内多公式', input: '\\(a\\) 和 \\(b\\)', expect: '$a$ 和 $b$' },
    {
      name: '未闭合 \\( 不吞后文',
      input: '段落 \\( 未闭合\n\n下一段 \\(x\\)',
      expect: '段落 \\( 未闭合\n\n下一段 $x$',
    },
    {
      name: '多行 \\(..\\) 升级为块级',
      input: '前文 \\(\nx = 1\n\\)\n后文',
      expect: '前文\n$$\nx = 1\n$$\n后文',
    },
  ];

  let ok = 0;
  for (const c of cases) {
    const got = transform(c.input).text;
    if (got === c.expect) {
      ok += 1;
    } else {
      console.log(`✗ ${c.name}`);
      console.log(`    期望：${JSON.stringify(c.expect)}`);
      console.log(`    实际：${JSON.stringify(got)}`);
    }
  }

  const sample = '前文 \\(a\\) 中\n\\[\n b = c\n\\]\n后文 $$d$$';
  const once = transform(sample).text;
  const twice = transform(once).text;
  const idem = once === twice;
  if (!idem) {
    console.log('✗ 幂等性');
    console.log(`    一次：${JSON.stringify(once)}`);
    console.log(`    二次：${JSON.stringify(twice)}`);
  }

  const total = cases.length + 1;
  const passed = ok + (idem ? 1 : 0);
  console.log(`${passed === total ? '✓' : '✗'} 自测：${passed}/${total} 通过`);
  return passed === total;
}

/* ============================== 主流程 ============================== */

function main() {
  const opts = parseArgs(process.argv.slice(2));

  if (opts.help) {
    printHelp();
    return 0;
  }
  if (opts.selfTest) {
    return runSelfTest() ? 0 : 1;
  }

  const files = collectFiles(opts.targets, opts.recursive);
  if (!files.length) {
    console.error('没有找到可处理的 Markdown 文件（*.md / *.markdown）。');
    return 2;
  }

  let changed = 0;
  let unchanged = 0;
  let failed = 0;
  const total = { block: 0, inline: 0, multilineInline: 0 };

  for (const file of files) {
    const rel = path.relative(process.cwd(), file) || file;
    let r;
    try {
      r = processFile(file, opts);
    } catch (err) {
      failed += 1;
      console.error(`✗ ${rel}：${err.message}`);
      continue;
    }

    total.block += r.stats.block;
    total.inline += r.stats.inline;
    total.multilineInline += r.stats.multilineInline;

    if (r.changed) {
      changed += 1;
      console.log(`${opts.dryRun ? '~' : '✓'} ${rel}  →  ${fmtStats(r.stats)}${opts.dryRun ? '（预览，未写入）' : ''}`);
      if (opts.dryRun || opts.verbose) {
        for (const s of r.samples) {
          console.log(`    - ${preview(s.before)}`);
          console.log(`    + ${preview(s.after)}`);
        }
      }
    } else {
      unchanged += 1;
      if (!opts.quiet) console.log(`· ${rel}  无需修改`);
    }

    for (const w of r.warnings) console.log(`    ! ${rel}：${w}`);
  }

  if (!opts.quiet) {
    console.log('');
    const verb = opts.dryRun ? '预览完成' : '处理完成';
    const parts = [`${verb}：${changed} 个文件${opts.dryRun ? '待修正' : '已修正'}`, `${unchanged} 个无需修改`];
    if (failed) parts.push(`${failed} 个失败`);
    console.log(parts.join('，'));
    if (total.block || total.inline || total.multilineInline) {
      const detail = [`块级 \\[..\\]→$$..$$：${total.block}`, `行内 \\(..\\)→$..$：${total.inline}`];
      if (total.multilineInline) detail.push(`多行行内→块级：${total.multilineInline}`);
      console.log(`合计：${detail.join('，')}`);
    }
    if (opts.dryRun) console.log('提示：去掉 -n / --dry-run 即可写入（默认自动生成 .bak 备份）。');
  }

  if (opts.check && changed) return 1;
  return failed ? 2 : 0;
}

process.exitCode = main();
