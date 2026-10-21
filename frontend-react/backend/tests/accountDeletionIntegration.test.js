const test = require("node:test");
const assert = require("node:assert/strict");

const adminPath = require.resolve("../firebaseAdmin");
const workerPath = require.resolve("../accountDeletionWorker");

async function runScenario({
  authFails = false,
  firestoreFails = false,
  partialFailure = false,
} = {}) {
  const state = {
    job: { status: "pending", attempts: 0 },
    authDeleted: false,
    recursiveDeletes: [],
    historyDocuments: partialFailure
      ? ["prediction-001", "prediction-002", "prediction-003"]
      : ["prediction-001"],
    failureTriggered: false,
  };

  const userRef = {
    async listCollections() {
      return [
        {
          name: "predictionHistory",
          limit() {
            return {
              async get() {
                const docs = state.historyDocuments.map((id) => ({
                  ref: { id },
                }));

                return {
                  empty: docs.length === 0,
                  docs,
                };
              },
            };
          },
        },
      ];
    },
  };

  const jobRef = {
    async get() {
      return {
        exists: true,
        data: () => ({ ...state.job }),
      };
    },
  };

  const db = {
    collection(name) {
      if (name === "accountDeletionJobs") {
        return {
          doc() {
            return jobRef;
          },
        };
      }

      if (name === "users") {
        return {
          doc() {
            return userRef;
          },
        };
      }

      throw new Error(`Unexpected collection: ${name}`);
    },

    async runTransaction(callback) {
      const pendingUpdates = [];

      const transaction = {
        async get() {
          return {
            exists: true,
            data: () => ({ ...state.job }),
          };
        },

        update(_ref, changes) {
          pendingUpdates.push(changes);
        },
      };

      const result = await callback(transaction);

      for (const changes of pendingUpdates) {
        state.job = {
          ...state.job,
          ...changes,
        };

        // Simulate Firestore converting Date values
        // into Timestamp objects when documents are read.
        if (state.job.leaseExpiresAt instanceof Date) {
          const milliseconds = state.job.leaseExpiresAt.getTime();

          state.job.leaseExpiresAt = {
            toMillis: () => milliseconds,
          };
        }
      }

      return result;
    },

    async recursiveDelete(ref) {
      if (
        partialFailure &&
        !state.failureTriggered &&
        state.recursiveDeletes.length === 1
      ) {
        state.failureTriggered = true;

        const error = new Error("Simulated partial cleanup failure");
        error.code = "firestore/unavailable";
        throw error;
      }

      if (firestoreFails) {
        const error = new Error("Simulated Firestore cleanup failure");
        error.code = "firestore/unavailable";
        throw error;
      }

      state.recursiveDeletes.push(ref.id);
      state.historyDocuments = state.historyDocuments.filter(
        (id) => id !== ref.id
      );
    },
  };

  const fakeAdmin = {
    firestore: () => db,

    auth: () => ({
      async deleteUser() {
        if (authFails) {
          const error = new Error("Simulated Authentication failure");
          error.code = "auth/internal-error";
          throw error;
        }

        state.authDeleted = true;
      },
    }),
  };

  const originalAdmin = require.cache[adminPath];
  const originalWorker = require.cache[workerPath];
  const originalTestUid = process.env.ACCOUNT_DELETION_TEST_UID;

  try {
    // These tests use a simulated account, never a real Firebase user.
    process.env.ACCOUNT_DELETION_TEST_UID = "test-user";
    require.cache[adminPath] = {
      id: adminPath,
      filename: adminPath,
      loaded: true,
      exports: {
        getFirebaseAdmin: () => fakeAdmin,
      },
    };

    delete require.cache[workerPath];

    const { processDeletionJob } = require(workerPath);

    const result = await processDeletionJob("test-user");

    if (partialFailure) {
      assert.equal(result.success, false);
      assert.equal(state.job.status, "failed");
      assert.equal(state.authDeleted, false);
      assert.deepEqual(state.historyDocuments, [
        "prediction-002",
        "prediction-003",
      ]);

      // Simulate the retry cooldown having expired.
      state.job.nextRetryAt = {
        toMillis: () => Date.now() - 1000,
      };

      const retryResult = await processDeletionJob("test-user");

      return { result: retryResult, state };
    }

    return { result, state };
  } finally {
    if (originalTestUid === undefined) {
      delete process.env.ACCOUNT_DELETION_TEST_UID;
    } else {
      process.env.ACCOUNT_DELETION_TEST_UID = originalTestUid;
    }

    delete require.cache[workerPath];

    if (originalWorker) {
      require.cache[workerPath] = originalWorker;
    }

    if (originalAdmin) {
      require.cache[adminPath] = originalAdmin;
    } else {
      delete require.cache[adminPath];
    }
  }
}

test("successful deletion completes the job", async () => {
  const { result, state } = await runScenario();

  assert.equal(result.success, true);
  assert.equal(state.authDeleted, true);
  assert.equal(state.job.status, "completed");
  assert.deepEqual(state.recursiveDeletes, ["prediction-001"]);
  assert.deepEqual(state.historyDocuments, []);
});

test("Authentication failure schedules a retry", async () => {
  const { result, state } = await runScenario({
    authFails: true,
  });

  assert.equal(result.success, false);
  assert.equal(state.authDeleted, false);
  assert.equal(state.job.status, "failed");
  assert.ok(state.job.nextRetryAt instanceof Date);
});


test("Firestore cleanup failure preserves Authentication account", async () => {
  const { result, state } = await runScenario({
    firestoreFails: true,
  });

  assert.equal(result.success, false);
  assert.equal(state.authDeleted, false);
  assert.equal(state.job.status, "failed");
  assert.equal(state.job.lastErrorCode, "firestore/unavailable");
  assert.ok(state.job.nextRetryAt instanceof Date);

  // The document remains because our simulated deletion failed.
  assert.deepEqual(state.historyDocuments, ["prediction-001"]);
});


test("partial Firestore deletion recovers on retry", async () => {
  const { result, state } = await runScenario({
    partialFailure: true,
  });

  assert.equal(result.success, true);
  assert.equal(state.authDeleted, true);
  assert.equal(state.job.status, "completed");

  assert.deepEqual(state.historyDocuments, []);

  assert.deepEqual(state.recursiveDeletes, [
    "prediction-001",
    "prediction-002",
    "prediction-003",
  ]);

  assert.equal(state.job.attempts, 2);
});
