import fs from 'node:fs';
import path from 'node:path';

const [asarPath, filter, outDir] = process.argv.slice(2);
const fd = fs.openSync(asarPath, 'r');
const sizeBuf = Buffer.alloc(8);
fs.readSync(fd, sizeBuf, 0, 8, 0);
const headerSize = sizeBuf.readUInt32LE(4);
const headerBuf = Buffer.alloc(headerSize);
fs.readSync(fd, headerBuf, 0, headerSize, 8);
const headerText = headerBuf.toString('utf8');
const start = headerText.indexOf('{');
const end = headerText.lastIndexOf('}');
const header = JSON.parse(headerText.slice(start, end + 1));
const base = 8 + headerSize;

let count = 0;
function walk(node, prefix) {
  for (const [name, value] of Object.entries(node.files || {})) {
    const p = prefix ? `${prefix}/${name}` : name;
    if (value.files) {
      walk(value, p);
      continue;
    }
    if (!p.includes(filter)) continue;
    if (value.unpacked) continue;
    const out = path.join(outDir, p.replace(/^dsh\//, ''));
    fs.mkdirSync(path.dirname(out), { recursive: true });
    const buf = Buffer.alloc(value.size);
    fs.readSync(fd, buf, 0, value.size, base + Number(value.offset));
    fs.writeFileSync(out, buf);
    count++;
  }
}
walk(header, '');
console.log(`extracted ${count} files to ${outDir}`);
