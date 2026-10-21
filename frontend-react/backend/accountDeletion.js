const express = require("express");
const { getFirebaseAdmin } = require("./firebaseAdmin");
const { createDeletionJob } = require("./accountDeletionJobs");

const router = express.Router();

router.post("/delete", async (req, res) => {
  if (process.env.ACCOUNT_DELETION_REQUESTS_ENABLED !== "true") {
    return res.status(503).json({
      error: "Account deletion is not available yet.",
      code: "ACCOUNT_DELETION_DISABLED",
    });
  }

  const authorization = req.headers.authorization || "";

  if (!authorization.startsWith("Bearer ")) {
    return res.status(401).json({
      error: "Authentication required.",
    });
  }

  const idToken = authorization.slice(7).trim();

  if (!idToken) {
    return res.status(401).json({
      error: "Authentication required.",
    });
  }

  try {
    const admin = getFirebaseAdmin();
    const decodedToken = await admin.auth().verifyIdToken(idToken, true);

    const authTime = Number(decodedToken.auth_time);
    const now = Math.floor(Date.now() / 1000);

    if (
      !Number.isFinite(authTime) ||
      now - authTime > 300 ||
      authTime > now + 60
    ) {
      return res.status(403).json({
        error: "Please verify your identity again.",
        code: "REAUTHENTICATION_REQUIRED",
      });
    }

    await createDeletionJob(decodedToken.uid);

    return res.status(202).json({
      success: true,
      status: "pending",
      message: "Account deletion request accepted.",
    });
  } catch (error) {
    console.error("Account deletion request failed:", {
      code: error.code || "unknown",
    });

    if (
      error.code === "auth/id-token-expired" ||
      error.code === "auth/argument-error" ||
      error.code === "auth/user-disabled" ||
      error.code === "auth/user-not-found" ||
      error.code === "auth/id-token-revoked"
    ) {
      return res.status(401).json({
        error: "Your session is invalid. Please sign in again.",
      });
    }

    return res.status(500).json({
      error: "Unable to request account deletion. Please try again.",
    });
  }
});

module.exports = router;
