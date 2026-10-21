const { getPendingDeletionJobs } = require("./accountDeletionJobs");
const { processDeletionJob } = require("./accountDeletionWorker");

const CHECK_INTERVAL_MS = 60 * 1000;
const MAX_JOBS_PER_RUN = 10;

let running = false;
let timer = null;

async function runDeletionRecovery() {
  if (running) {
    return;
  }

  running = true;

  try {
    // Reserve capacity for new requests and recovery jobs.
    // This prevents pending jobs from monopolising every cycle.
    const allocations = [
      { status: "pending", limit: 4 },
      { status: "failed", limit: 3 },
      { status: "processing", limit: 3 },
    ];

    const jobs = [];

    for (const allocation of allocations) {
      const selected = await getPendingDeletionJobs(
        allocation.limit,
        [allocation.status]
      );

      jobs.push(...selected);
    }

    // Monitor deletion jobs requiring manual intervention.
    const db = require("./firebaseAdmin").getFirebaseAdmin().firestore();

    const attentionSnapshot = await db
      .collection("accountDeletionJobs")
      .where("status", "==", "needs_attention")
      .count()
      .get();

    const attentionCount = attentionSnapshot.data().count;

    if (attentionCount > 0) {
      console.error(
        `ACCOUNT DELETION ALERT: ${attentionCount} jobs require manual attention.`
      );
    }

    for (const job of jobs) {
      try {
        const result = await processDeletionJob(job.uid);

        if (result.processed) {
          console.log("Account deletion job processed:", {
            success: result.success,
          });
        }
      } catch (error) {
        console.error("Account deletion recovery error:", {
          code: error.code || "unknown",
        });
      }
    }
  } catch (error) {
    console.error("Account deletion scheduler error:", {
      code: error.code || "unknown",
    });
  } finally {
    running = false;
  }
}

function startDeletionScheduler() {
  if (process.env.ACCOUNT_DELETION_WORKER_ENABLED !== "true") {
    console.log("Account deletion worker is disabled.");
    return;
  }

  if (timer) {
    return;
  }

  console.log("Account deletion recovery scheduler started.");

  timer = setInterval(() => {
    void runDeletionRecovery();
  }, CHECK_INTERVAL_MS);

  timer.unref();
}

module.exports = {
  startDeletionScheduler,
  runDeletionRecovery,
};
