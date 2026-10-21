const {
  initializeApp,
  getApps,
  getApp,
  applicationDefault,
} = require("firebase-admin/app");

const { getAuth } = require("firebase-admin/auth");
const { getFirestore } = require("firebase-admin/firestore");

function getFirebaseAdmin() {
  if (getApps().length === 0) {
    initializeApp({
      credential: applicationDefault(),
      projectId: "bushfire-ai-platform",
    });
  }

  const app = getApp();

  return {
    app: () => app,
    auth: () => getAuth(app),
    firestore: () => getFirestore(app),
  };
}

module.exports = { getFirebaseAdmin };
