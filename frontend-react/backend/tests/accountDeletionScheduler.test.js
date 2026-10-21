const test = require("node:test");
const assert = require("node:assert/strict");

const jobsPath = require.resolve("../accountDeletionJobs");
const workerPath = require.resolve("../accountDeletionWorker");
const schedulerPath = require.resolve("../accountDeletionScheduler");

test("scheduler reserves capacity for all three job categories", async () => {
  const selections = [];
  const processed = [];

  const originalJobs = require.cache[jobsPath];
  const originalWorker = require.cache[workerPath];
  const originalScheduler = require.cache[schedulerPath];

  try {
    require.cache[jobsPath] = {
      id: jobsPath,
      filename: jobsPath,
      loaded: true,
      exports: {
        getPendingDeletionJobs: async (limit, statuses) => {
          selections.push({ limit, statuses });

          return Array.from({ length: limit }, (_, index) => ({
            uid: `${statuses[0]}-${index}`,
          }));
        },
      },
    };

    require.cache[workerPath] = {
      id: workerPath,
      filename: workerPath,
      loaded: true,
      exports: {
        processDeletionJob: async (uid) => {
          processed.push(uid);

          return {
            processed: true,
            success: true,
          };
        },
      },
    };

    delete require.cache[schedulerPath];

    const { runDeletionRecovery } = require(schedulerPath);

    await runDeletionRecovery();

    assert.deepEqual(selections, [
      { limit: 4, statuses: ["pending"] },
      { limit: 3, statuses: ["failed"] },
      { limit: 3, statuses: ["processing"] },
    ]);

    assert.equal(processed.length, 10);

    assert.equal(
      processed.filter((uid) => uid.startsWith("pending-")).length,
      4
    );

    assert.equal(
      processed.filter((uid) => uid.startsWith("failed-")).length,
      3
    );

    assert.equal(
      processed.filter((uid) => uid.startsWith("processing-")).length,
      3
    );
  } finally {
    for (const [path, original] of [
      [jobsPath, originalJobs],
      [workerPath, originalWorker],
      [schedulerPath, originalScheduler],
    ]) {
      if (original) {
        require.cache[path] = original;
      } else {
        delete require.cache[path];
      }
    }
  }
});
