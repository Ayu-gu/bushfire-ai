const { randomUUID } = require("node:crypto");
const { getFirebaseAdmin } = require("./firebaseAdmin");

const LEASE_MS = 5 * 60 * 1000;
const BATCH_SIZE = 200;

async function claimJob(uid) {
  const db = getFirebaseAdmin().firestore();
  const jobRef = db.collection("accountDeletionJobs").doc(uid);
  const leaseId = randomUUID();

  return db.runTransaction(async (transaction) => {
    const snapshot = await transaction.get(jobRef);

    if (!snapshot.exists) {
      return null;
    }

    const job = snapshot.data();
    const now = Date.now();

    const claimableStatuses = new Set([
      "pending",
      "failed",
      "processing",
    ]);

    if (!claimableStatuses.has(job.status)) {
      return null;
    }

    if (
      job.status === "processing" &&
      job.leaseExpiresAt?.toMillis() > now
    ) {
      return null;
    }

    if (
      job.status === "failed" &&
      job.nextRetryAt?.toMillis() > now
    ) {
      return null;
    }

    if ((job.attempts || 0) >= 5) {
      transaction.update(jobRef, {
        status: "needs_attention",
        updatedAt: new Date(),
        leaseId: null,
        leaseExpiresAt: null,
      });

      return null;
    }

    transaction.update(jobRef, {
      status: "processing",
      leaseId,
      leaseExpiresAt: new Date(now + LEASE_MS),
      attempts: (job.attempts || 0) + 1,
      updatedAt: new Date(),
    });

    return leaseId;
  });
}

async function renewLease(uid, leaseId) {
  const db = getFirebaseAdmin().firestore();
  const jobRef = db.collection("accountDeletionJobs").doc(uid);

  return db.runTransaction(async (transaction) => {
    const snapshot = await transaction.get(jobRef);

    const job = snapshot.data();
    const now = Date.now();

    if (
      !snapshot.exists ||
      job.status !== "processing" ||
      job.leaseId !== leaseId ||
      !job.leaseExpiresAt ||
      job.leaseExpiresAt.toMillis() <= now
    ) {
      return false;
    }

    transaction.update(jobRef, {
      leaseExpiresAt: new Date(now + LEASE_MS),
      updatedAt: new Date(),
    });

    return true;
  });
}

async function assertLeaseOwnership(uid, leaseId) {
  const db = getFirebaseAdmin().firestore();
  const snapshot = await db
    .collection("accountDeletionJobs")
    .doc(uid)
    .get();

  const job = snapshot.data();

  if (
    !job ||
    job.status !== "processing" ||
    job.leaseId !== leaseId ||
    !job.leaseExpiresAt ||
    job.leaseExpiresAt.toMillis() <= Date.now()
  ) {
    throw new Error("Deletion worker no longer owns this job.");
  }
}

async function deleteCollection(db, collectionRef, uid, leaseId) {
  while (true) {
    await assertLeaseOwnership(uid, leaseId);

    const snapshot = await collectionRef.limit(BATCH_SIZE).get();

    if (snapshot.empty) {
      return;
    }

    for (const document of snapshot.docs) {
      await assertLeaseOwnership(uid, leaseId);

      // Delete this document and every nested subcollection.
      // Never call recursiveDelete on the user's parent document:
      // its deletion marker must remain in place.
      await db.recursiveDelete(document.ref);
    }
  }
}

async function processDeletionJob(uid) {
  const leaseId = await claimJob(uid);

  if (!leaseId) {
    return { processed: false };
  }

  const admin = getFirebaseAdmin();
  const db = admin.firestore();
  const jobRef = db.collection("accountDeletionJobs").doc(uid);
  const userRef = db.collection("users").doc(uid);

  let leaseValid = true;

  const heartbeat = setInterval(async () => {
    try {
      const renewed = await renewLease(uid, leaseId);

      if (!renewed) {
        leaseValid = false;
      }
    } catch (error) {
      leaseValid = false;
      console.error("Deletion lease renewal failed:", error.message);
    }
  }, 60 * 1000);

  heartbeat.unref();

  try {
    // Discover all subcollections belonging to this user.
    const subcollections = await userRef.listCollections();

    for (const collectionRef of subcollections) {
      await assertLeaseOwnership(uid, leaseId);

      await deleteCollection(
        db,
        collectionRef,
        uid,
        leaseId
      );
    }

    if (!leaseValid) {
      throw new Error("Deletion worker lost its lease.");
    }

    await assertLeaseOwnership(uid, leaseId);

    try {
      await admin.auth().deleteUser(uid);
    } catch (error) {
      if (error.code !== "auth/user-not-found") {
        throw error;
      }
    }

    // Keep the deletion marker after Authentication deletion.
    // Existing ID tokens may remain valid until they expire.
    // A separate retention-based cleanup process will remove
    // this marker once it is safe to do so.

    const completed = await db.runTransaction(async (transaction) => {
      const snapshot = await transaction.get(jobRef);

      const job = snapshot.data();

      if (
        !snapshot.exists ||
        job.status !== "processing" ||
        job.leaseId !== leaseId ||
        !job.leaseExpiresAt ||
        job.leaseExpiresAt.toMillis() <= Date.now()
      ) {
        return false;
      }

      transaction.update(jobRef, {
        status: "completed",
        completedAt: new Date(),
        updatedAt: new Date(),
        leaseId: null,
        leaseExpiresAt: null,
      });

      return true;
    });

    if (!completed) {
      return { processed: true, success: false, leaseLost: true };
    }

    return { processed: true, success: true };
  } catch (error) {
    console.error("Deletion worker failed:", {
      code: error.code || "unknown",
    });

    await db.runTransaction(async (transaction) => {
      const snapshot = await transaction.get(jobRef);

      if (!snapshot.exists || snapshot.data().leaseId !== leaseId) {
        return;
      }

      const attempts = snapshot.data().attempts || 1;
      const exhausted = attempts >= 5;
      const retryDelay = Math.min(
        60 * 1000 * (2 ** Math.max(0, attempts - 1)),
        60 * 60 * 1000
      );

      transaction.update(jobRef, {
        status: exhausted ? "needs_attention" : "failed",
        updatedAt: new Date(),
        leaseId: null,
        leaseExpiresAt: null,
        nextRetryAt: exhausted
          ? null
          : new Date(Date.now() + retryDelay),
        lastErrorCode: error.code || "unknown",
      });
    });

    return { processed: true, success: false };
  } finally {
    clearInterval(heartbeat);
  }
}

module.exports = {
  processDeletionJob,
  claimJob,
  renewLease,
  assertLeaseOwnership,
};
