import fs from "node:fs";
const p = process.argv[2];
const fd = fs.openSync(p, "r");
const b = Buffer.alloc(24);
fs.readSync(fd, b, 0, 24, 0);
console.log("first24hex", b.toString("hex"));
console.log("u32@0", b.readUInt32LE(0), "u32@4", b.readUInt32LE(4), "u32@8", b.readUInt32LE(8), "u32@12", b.readUInt32LE(12));
