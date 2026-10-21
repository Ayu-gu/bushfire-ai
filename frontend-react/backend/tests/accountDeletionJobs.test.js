const test = require("node:test");
const assert = require("node:assert/strict");

const adminPath = require.resolve("../firebaseAdmin");
const jobsPath = require.resolve("../accountDeletionJobs");

function timestamp(milliseconds) {
  return { toMillis: () => milliseconds };
}

async function selectJobs(jobs, limit = 10) {
  const fakeCollection = {
    where(_field, _operator, status) {
      let cursor = null;
      let pageSize = 100;

      const query = {
        orderBy() {
          return query;
        },

        limit(value) {
          pageSize = value;
          return query;
        },

        startAfter(document) {
          cursor = document.id;
          return query;
        },

        async get() {
          const matching = jobs
            .filter((job) => job.status === status)
            .sort((a, b) => a.id.localeCompare(b.id));

          const start = cursor
            ? matching.findIndex((job) => job.id === cursor) + 1
            : 0;

          const docs = matching.slice(start, start + pageSize)
            .map((job) => ({
              id: job.id,
              data: () => ({ ...job }),
            }));

          return {
            empty: docs.length === 0,
            size: docs.length,
            docs,
          };
        },
      };

      return query;
    },
  };

  const fakeAdmin = {
    firestore: () => ({
      collection: () => fakeCollection,
    }),
  };

  const originalAdmin = require.cache[adminPath];
  const originalJobs = require.cache[jobsPath];

  try {
    require.cache[adminPath] = {
      id: adminPath,
      filename: adminPath,
      loaded: true,
      exports: {
        getFirebaseAdmin: () => fakeAdmin,
      },
    };

    delete require.cache[jobsPath];

    const { getPendingDeletionJobs } = require(jobsPath);

    return await getPendingDeletionJobs(limit);
  } finally {
    if (originalJobs) {
      require.cache[jobsPath] = originalJobs;
    } else {
      delete require.cache[jobsPath];
    }

    if (originalAdmin) {
      require.cache[adminPath] = originalAdmin;
    } else {
      delete require.cache[adminPath];
    }
  }
}

test("selects pending jobs", async () => {
  const selected = await selectJobs([
    { id: "A", status: "pending", attempts: 0 },
  ]);

  assert.deepEqual(selected.map((job) => job.id), ["A"]);
});

test("skips active retry cooldowns", async () => {
  const selected = await selectJobs([
    {
      id: "A",
      status: "failed",
      attempts: 1,
      nextRetryAt: timestamp(Date.now() + 60000),
    },
    {
      id: "B",
      status: "failed",
      attempts: 1,
      nextRetryAt: timestamp(Date.now() - 60000),
    },
  ]);

  assert.deepEqual(selected.map((job) => job.id), ["B"]);
});

test("skips active leases and selects expired leases", async () => {
  const selected = await selectJobs([
    {
      id: "A",
      status: "processing",
      attempts: 1,
      leaseExpiresAt: timestamp(Date.now() + 60000),
    },
    {
      id: "B",
      status: "processing",
      attempts: 1,
      leaseExpiresAt: timestamp(Date.now() - 60000),
    },
  ]);

  assert.deepEqual(selected.map((job) => job.id), ["B"]);
});

test("excludes exhausted jobs", async () => {
  const selected = await selectJobs([
    { id: "A", status: "pending", attempts: 5 },
    { id: "B", status: "pending", attempts: 1 },
  ]);

  assert.deepEqual(selected.map((job) => job.id), ["B"]);
});

test("paginates past ineligible jobs", async () => {
  const jobs = Array.from({ length: 105 }, (_, index) => ({
    id: `job-${String(index).padStart(3, "0")}`,
    status: "failed",
    attempts: 1,
    nextRetryAt: timestamp(
      Date.now() + (index < 100 ? 60000 : -60000)
    ),
  }));

  const selected = await selectJobs(jobs, 5);

  assert.deepEqual(
    selected.map((job) => job.id),
    [
      "job-100",
      "job-101",
      "job-102",
      "job-103",
      "job-104",
    ]
  );
});
