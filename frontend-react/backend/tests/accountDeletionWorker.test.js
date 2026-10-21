const test = require("node:test");
const assert = require("node:assert/strict");
const Module = require("node:module");

const adminPath = require.resolve("../firebaseAdmin");
const workerPath = require.resolve("../accountDeletionWorker");

function createFakeFirestore(initialJob) {
  let job = { ...initialJob };

  const ref = {
    async get() {
      return {
        exists: job !== null,
        data: () => job,
      };
    },
  };

  const db = {
    collection(name) {
      assert.equal(name, "accountDeletionJobs");

      return {
        doc(uid) {
          assert.equal(uid, "test-user");
          return ref;
        },
      };
    },

    async runTransaction(callback) {
      const pendingUpdates = [];

      const transaction = {
        async get() {
          return {
            exists: job !== null,
            data: () => ({ ...job }),
          };
        },

        update(_ref, changes) {
          pendingUpdates.push(changes);
        },
      };

      // Only commit writes after the callback succeeds.
      const result = await callback(transaction);

      for (const changes of pendingUpdates) {
        job = {
          ...job,
          ...changes,
        };
      }

      return result;
    },
  };

  return {
    db,
    getJob: () => job,
  };
}

async function withFakeWorker(initialJob, callback) {
  const fake = createFakeFirestore(initialJob);

  const originalAdminCache = require.cache[adminPath];
  const originalWorkerCache = require.cache[workerPath];

  try {
    require.cache[adminPath] = {
      id: adminPath,
      filename: adminPath,
      loaded: true,
      exports: {
        getFirebaseAdmin: () => ({
          firestore: () => fake.db,
        }),
      },
    };

    delete require.cache[workerPath];

    const worker = require(workerPath);

    await callback(worker, fake);
  } finally {
    delete require.cache[workerPath];

    if (originalWorkerCache) {
      require.cache[workerPath] = originalWorkerCache;
    }

    if (originalAdminCache) {
      require.cache[adminPath] = originalAdminCache;
    } else {
      delete require.cache[adminPath];
    }
  }
}

function timestamp(milliseconds) {
  return {
    toMillis: () => milliseconds,
  };
}

test("pending job can be claimed", async () => {
  await withFakeWorker(
    { status: "pending", attempts: 0 },
    async (worker, fake) => {
      const leaseId = await worker.claimJob("test-user");

      assert.equal(typeof leaseId, "string");
      assert.equal(fake.getJob().status, "processing");
      assert.equal(fake.getJob().attempts, 1);
    }
  );
});

test("active processing job cannot be claimed twice", async () => {
  await withFakeWorker(
    {
      status: "processing",
      attempts: 1,
      leaseId: "existing-worker",
      leaseExpiresAt: timestamp(Date.now() + 60000),
    },
    async (worker) => {
      const leaseId = await worker.claimJob("test-user");
      assert.equal(leaseId, null);
    }
  );
});

test("expired processing job can be recovered", async () => {
  await withFakeWorker(
    {
      status: "processing",
      attempts: 1,
      leaseId: "old-worker",
      leaseExpiresAt: timestamp(Date.now() - 60000),
    },
    async (worker, fake) => {
      const leaseId = await worker.claimJob("test-user");

      assert.equal(typeof leaseId, "string");
      assert.notEqual(leaseId, "old-worker");
      assert.equal(fake.getJob().attempts, 2);
    }
  );
});

test("failed job respects retry cooldown", async () => {
  await withFakeWorker(
    {
      status: "failed",
      attempts: 2,
      nextRetryAt: timestamp(Date.now() + 60000),
    },
    async (worker) => {
      const leaseId = await worker.claimJob("test-user");
      assert.equal(leaseId, null);
    }
  );
});

test("job stops after maximum attempts", async () => {
  await withFakeWorker(
    {
      status: "failed",
      attempts: 5,
    },
    async (worker, fake) => {
      const leaseId = await worker.claimJob("test-user");

      assert.equal(leaseId, null);
      assert.equal(fake.getJob().status, "needs_attention");
    }
  );
});

test("valid worker can renew its lease", async () => {
  await withFakeWorker(
    {
      status: "processing",
      attempts: 1,
      leaseId: "worker-123",
      leaseExpiresAt: timestamp(Date.now() + 60000),
    },
    async (worker, fake) => {
      const renewed = await worker.renewLease(
        "test-user",
        "worker-123"
      );

      assert.equal(renewed, true);

      const expiry = fake.getJob().leaseExpiresAt.getTime();

      assert.ok(expiry > Date.now() + 240000);
    }
  );
});

test("expired lease cannot be renewed", async () => {
  await withFakeWorker(
    {
      status: "processing",
      attempts: 1,
      leaseId: "worker-123",
      leaseExpiresAt: timestamp(Date.now() - 60000),
    },
    async (worker) => {
      const renewed = await worker.renewLease(
        "test-user",
        "worker-123"
      );

      assert.equal(renewed, false);
    }
  );
});

test("worker cannot renew another worker's lease", async () => {
  await withFakeWorker(
    {
      status: "processing",
      attempts: 1,
      leaseId: "worker-A",
      leaseExpiresAt: timestamp(Date.now() + 60000),
    },
    async (worker) => {
      const renewed = await worker.renewLease(
        "test-user",
        "worker-B"
      );

      assert.equal(renewed, false);
    }
  );
});

test("worker that lost ownership cannot continue", async () => {
  await withFakeWorker(
    {
      status: "processing",
      attempts: 2,
      leaseId: "worker-B",
      leaseExpiresAt: timestamp(Date.now() + 60000),
    },
    async (worker) => {
      await assert.rejects(
        worker.assertLeaseOwnership(
          "test-user",
          "worker-A"
        ),
        /no longer owns/
      );
    }
  );
});
