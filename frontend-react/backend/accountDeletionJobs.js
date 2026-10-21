const { getFirebaseAdmin } = require("./firebaseAdmin");

const JOB_COLLECTION = "accountDeletionJobs";

function getDeletionJobRef(uid) {
  const admin = getFirebaseAdmin();

  return admin.firestore()
    .collection(JOB_COLLECTION)
    .doc(uid);
}

async function createDeletionJob(uid) {
  if (typeof uid !== "string" || !uid.trim()) {
    throw new Error("A valid user ID is required.");
  }

  const admin = getFirebaseAdmin();
  const db = admin.firestore();

  const jobRef = getDeletionJobRef(uid);
  const userRef = db.collection("users").doc(uid);

  const now = new Date();

  await db.runTransaction(async (transaction) => {
    const existingJob = await transaction.get(jobRef);

    if (existingJob.exists) {
      if (existingJob.data().status === "completed") {
        throw new Error("Account deletion already completed.");
      }

      // Restore the deletion marker if an unfinished job
      // already exists. This keeps client writes blocked.
      transaction.set(
        userRef,
        {
          deletionStatus: "deleting",
        },
        { merge: true }
      );

      return;
    }

    transaction.set(jobRef, {
      uid,
      status: "pending",
      createdAt: now,
      updatedAt: now,
      attempts: 0,
    });

    transaction.set(
      userRef,
      {
        deletionStatus: "deleting",
        deletionRequestedAt: now,
      },
      { merge: true }
    );
  });

  return jobRef;
}

async function updateDeletionJob(uid, status, details = {}) {
  const jobRef = getDeletionJobRef(uid);

  await jobRef.update({
    status,
    ...details,
    updatedAt: new Date(),
  });
}

async function getPendingDeletionJobs(limit = 20, allowedStatuses = null) {
  if (!Number.isInteger(limit) || limit < 1) {
    throw new Error("Job limit must be a positive integer.");
  }

  const validStatuses = ["pending", "failed", "processing"];

  if (
    allowedStatuses !== null &&
    (
      !Array.isArray(allowedStatuses) ||
      allowedStatuses.length === 0 ||
      allowedStatuses.some((status) => !validStatuses.includes(status))
    )
  ) {
    throw new Error("Invalid deletion job statuses.");
  }

  const db = getFirebaseAdmin().firestore();
  const collection = db.collection(JOB_COLLECTION);

  const now = Date.now();
  const readyJobs = [];

  const statuses = allowedStatuses || validStatuses;

  // Read each status separately so pending jobs receive priority.
  for (const status of statuses) {
    let lastDocument = null;

    while (readyJobs.length < limit) {
      let query = collection
        .where("status", "==", status)
        .orderBy("__name__")
        .limit(100);

      if (lastDocument) {
        query = query.startAfter(lastDocument);
      }

      const snapshot = await query.get();

      if (snapshot.empty) {
        break;
      }

      for (const doc of snapshot.docs) {
        const job = doc.data();

        if ((job.attempts || 0) >= 5) {
          continue;
        }

        if (
          status === "failed" &&
          job.nextRetryAt?.toMillis() > now
        ) {
          continue;
        }

        if (
          status === "processing" &&
          job.leaseExpiresAt?.toMillis() > now
        ) {
          continue;
        }

        readyJobs.push({
          id: doc.id,
          ...job,
        });

        if (readyJobs.length >= limit) {
          break;
        }
      }

      if (snapshot.size < 100) {
        break;
      }

      lastDocument = snapshot.docs[snapshot.docs.length - 1];
    }

    if (readyJobs.length >= limit) {
      break;
    }
  }

  return readyJobs;
}

module.exports = {
  createDeletionJob,
  updateDeletionJob,
  getPendingDeletionJobs,
};
