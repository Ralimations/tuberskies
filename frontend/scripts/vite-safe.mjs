import childProcess from "node:child_process";
import { syncBuiltinESMExports } from "node:module";
import { EventEmitter } from "node:events";

function createStubProcess() {
  const proc = new EventEmitter();
  proc.pid = undefined;
  proc.stdin = null;
  proc.stdout = null;
  proc.stderr = null;
  proc.kill = () => false;
  return proc;
}

const originalExec = childProcess.exec.bind(childProcess);

childProcess.exec = function patchedExec(command, options, callback) {
  const cb = typeof options === "function" ? options : callback;
  const normalized = String(command || "").trim().toLowerCase();
  if (normalized === "net use") {
    const stub = createStubProcess();
    queueMicrotask(() => {
      if (typeof cb === "function") {
        cb(null, "", "");
      }
      stub.emit("exit", 0);
      stub.emit("close", 0);
    });
    return stub;
  }

  try {
    return originalExec(command, options, callback);
  } catch (error) {
    if (normalized === "net use" && error instanceof Error && /eperm/i.test(error.message)) {
      const stub = createStubProcess();
      queueMicrotask(() => {
        if (typeof cb === "function") {
          cb(null, "", "");
        }
        stub.emit("exit", 0);
        stub.emit("close", 0);
      });
      return stub;
    }
    throw error;
  }
};

syncBuiltinESMExports();

const argv = process.argv.slice(2);
if (!argv.includes("--configLoader")) {
  argv.push("--configLoader", "native");
}
process.argv = [process.argv[0], process.argv[1], ...argv];

await import(new URL("../node_modules/vite/bin/vite.js", import.meta.url));
