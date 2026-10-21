const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const backend = path.resolve(__dirname, "..");

function read(filename) {
  return fs.readFileSync(path.join(backend, filename), "utf8");
}

const api = read("accountDeletion.js");
const jobs = read("accountDeletionJobs.js");
const worker = read("accountDeletionWorker.js");
const scheduler = read("accountDeletionScheduler.js");
const server = read("server.js");

assert.match(
  api,
  /verifyIdToken\(idToken,\s*true\)/,
  "API must verify Firebase ID tokens."
);

assert.match(
  api,
  /auth_time/,
  "API must check recent authentication."
);

assert.match(
  jobs,
  /runTransaction/,
  "Deletion jobs must be created transactionally."
);

assert.match(
  worker,
  /recursiveDelete/,
  "Worker must recursively delete nested Firestore data."
);

assert.match(
  worker,
  /assertLeaseOwnership/,
  "Worker must verify lease ownership."
);

assert.match(
  worker,
  /needs_attention/,
  "Worker must limit repeated failures."
);

assert.match(
  scheduler,
  /ACCOUNT_DELETION_WORKER_ENABLED/,
  "Scheduler must be disabled unless explicitly enabled."
);

assert.match(
  server,
  /startDeletionScheduler\(\)/,
  "Express must initialise the scheduler."
);

console.log("PASS: All 8 account-deletion structural checks.");
console.log("No Firebase connections or deletion operations were performed.");
