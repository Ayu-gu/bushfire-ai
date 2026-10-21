const test = require("node:test");
const assert = require("node:assert/strict");
const express = require("express");

const routerPath = require.resolve("../accountDeletion");
const jobsPath = require.resolve("../accountDeletionJobs");
const adminPath = require.resolve("../firebaseAdmin");

test("deletion endpoint rejects requests when feature is disabled", async () => {
  const previousFlag = process.env.ACCOUNT_DELETION_REQUESTS_ENABLED;
  const originalRouter = require.cache[routerPath];
  const originalJobs = require.cache[jobsPath];
  const originalAdmin = require.cache[adminPath];

  let firebaseCalled = false;

  try {
    delete process.env.ACCOUNT_DELETION_REQUESTS_ENABLED;

    require.cache[jobsPath] = {
      id: jobsPath,
      filename: jobsPath,
      loaded: true,
      exports: {
        createDeletionJob: async () => {
          firebaseCalled = true;
        },
      },
    };

    require.cache[adminPath] = {
      id: adminPath,
      filename: adminPath,
      loaded: true,
      exports: {
        getFirebaseAdmin: () => {
          firebaseCalled = true;
          throw new Error("Firebase should not be called");
        },
      },
    };

    delete require.cache[routerPath];

    const app = express();
    app.use("/api/account", require(routerPath));

    const server = app.listen(0);

    try {
      await new Promise((resolve) => {
        if (server.listening) resolve();
        else server.once("listening", resolve);
      });

      const address = server.address();

      const response = await fetch(
        `http://127.0.0.1:${address.port}/api/account/delete`,
        {
          method: "POST",
          headers: {
            Authorization: "Bearer fake-token",
          },
        }
      );

      const body = await response.json();

      assert.equal(response.status, 503);
      assert.equal(body.code, "ACCOUNT_DELETION_DISABLED");
      assert.equal(firebaseCalled, false);
    } finally {
      await new Promise((resolve) => server.close(resolve));
    }
  } finally {
    if (previousFlag === undefined) {
      delete process.env.ACCOUNT_DELETION_REQUESTS_ENABLED;
    } else {
      process.env.ACCOUNT_DELETION_REQUESTS_ENABLED = previousFlag;
    }

    for (const [path, original] of [
      [routerPath, originalRouter],
      [jobsPath, originalJobs],
      [adminPath, originalAdmin],
    ]) {
      if (original) require.cache[path] = original;
      else delete require.cache[path];
    }
  }
});
