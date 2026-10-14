import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import {
  ArrowLeft,
  LockKeyhole,
  Mail,
  ShieldCheck,
  X,
} from "lucide-react";

import {
  createUserWithEmailAndPassword,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  updateProfile,
} from "firebase/auth";

import { auth, googleProvider } from "../firebase";
import "./AuthModal.css";

export default function AuthModal({ isOpen, onClose }) {
  const [mode, setMode] = useState("signin");

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");

  const isSignUp = mode === "signup";
  const isReset = mode === "reset";

  const changeMode = (newMode) => {
    setMode(newMode);
    setAuthError("");
    setAuthSuccess("");
    setPassword("");
    setConfirmPassword("");
  };

  const getAuthErrorMessage = (error) => {
    switch (error.code) {
      case "auth/email-already-in-use":
        return "An account already exists with this email address.";

      case "auth/invalid-email":
        return "Please enter a valid email address.";

      case "auth/weak-password":
        return "Please choose a stronger password.";

      case "auth/invalid-credential":
      case "auth/wrong-password":
      case "auth/user-not-found":
        return "Incorrect email or password.";

      case "auth/too-many-requests":
        return "Too many attempts. Please try again later.";

      case "auth/network-request-failed":
        return "Network error. Please check your internet connection.";

      case "auth/unauthorized-domain":
        return "This website is not authorised in Firebase Authentication.";

      default:
        return "Something went wrong. Please try again.";
    }
  };

  const handleGoogleSignIn = async () => {
    setAuthLoading(true);
    setAuthError("");
    setAuthSuccess("");

    try {
      await signInWithPopup(auth, googleProvider);
      onClose();
    } catch (error) {
      if (error.code !== "auth/popup-closed-by-user") {
        console.error("Google sign-in failed:", error.code);
        setAuthError(getAuthErrorMessage(error));
      }
    } finally {
      setAuthLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (authLoading) return;

    setAuthLoading(true);
    setAuthError("");
    setAuthSuccess("");

    try {
      // PASSWORD RESET
      if (isReset) {
        await sendPasswordResetEmail(auth, email.trim());

        setAuthSuccess(
          "If an account exists for this email, you will receive password reset instructions."
        );

        return;
      }

      // CREATE ACCOUNT
      if (isSignUp) {
        if (!fullName.trim()) {
          setAuthError("Please enter your full name.");
          return;
        }

        if (password !== confirmPassword) {
          setAuthError("Passwords do not match.");
          return;
        }

        if (password.length < 8) {
          setAuthError("Password must contain at least 8 characters.");
          return;
        }

        const result = await createUserWithEmailAndPassword(
          auth,
          email.trim(),
          password
        );

        await updateProfile(result.user, {
          displayName: fullName.trim(),
        });

        try {
          await sendEmailVerification(result.user);
        } catch (verificationError) {
          console.error(
            "Verification email failed:",
            verificationError.code
          );
        }

        onClose();
        return;
      }

      // EMAIL SIGN IN
      await signInWithEmailAndPassword(
        auth,
        email.trim(),
        password
      );

      onClose();
    } catch (error) {
      console.error("Firebase authentication error:", error.code);
      setAuthError(getAuthErrorMessage(error));
    } finally {
      setAuthLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (event) => {
      if (event.key === "Escape" && !authLoading) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, onClose, authLoading]);

  if (!isOpen) return null;

  return createPortal(
    <div
      className="auth-overlay"
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget &&
          !authLoading
        ) {
          onClose();
        }
      }}
    >
      <section
        className="auth-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-title"
      >
        <button
          className="auth-close"
          type="button"
          onClick={onClose}
          disabled={authLoading}
          aria-label="Close authentication"
        >
          <X size={19} />
        </button>

        <div className="auth-brand">
          <img src="/bushfire-icon.svg" alt="" />
          <span>Bushfire AI</span>
        </div>

        <div className="auth-heading">
          <h2 id="auth-title">
            {isReset
              ? "Reset your password"
              : isSignUp
                ? "Create your account"
                : "Welcome back"}
          </h2>

          <p>
            {isReset
              ? "Enter your email to receive password reset instructions."
              : isSignUp
                ? "Create an account to save locations and track your bushfire risk assessments."
                : "Sign in to access your saved locations and prediction history."}
          </p>
        </div>

        {!isReset && (
          <>
            <button
              className="auth-google"
              type="button"
              onClick={handleGoogleSignIn}
              disabled={authLoading}
            >
              <span className="auth-google-mark">G</span>
              {authLoading
                ? "Please wait..."
                : "Continue with Google"}
            </button>

            <div className="auth-divider">
              <span>or continue with email</span>
            </div>
          </>
        )}

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >
          {isSignUp && (
            <>
              <label htmlFor="auth-name">
                Full name
              </label>

              <div className="auth-input-wrap">
                <input
                  id="auth-name"
                  type="text"
                  placeholder="Enter your full name"
                  autoComplete="name"
                  value={fullName}
                  onChange={(event) =>
                    setFullName(event.target.value)
                  }
                  disabled={authLoading}
                  required
                />
              </div>
            </>
          )}

          <label htmlFor="auth-email">
            Email address
          </label>

          <div className="auth-input-wrap">
            <Mail size={17} />

            <input
              id="auth-email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              disabled={authLoading}
              required
            />
          </div>

          {!isReset && (
            <>
              <label htmlFor="auth-password">
                Password
              </label>

              <div className="auth-input-wrap">
                <LockKeyhole size={17} />

                <input
                  id="auth-password"
                  type="password"
                  placeholder="Enter your password"
                  autoComplete={
                    isSignUp
                      ? "new-password"
                      : "current-password"
                  }
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  minLength={isSignUp ? 8 : 6}
                  disabled={authLoading}
                  required
                />
              </div>
            </>
          )}

          {isSignUp && (
            <>
              <label htmlFor="auth-confirm-password">
                Confirm password
              </label>

              <div className="auth-input-wrap">
                <LockKeyhole size={17} />

                <input
                  id="auth-confirm-password"
                  type="password"
                  placeholder="Confirm your password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) =>
                    setConfirmPassword(event.target.value)
                  }
                  disabled={authLoading}
                  required
                />
              </div>
            </>
          )}

          {!isSignUp && !isReset && (
            <button
              className="auth-text-button auth-forgot"
              type="button"
              onClick={() => changeMode("reset")}
              disabled={authLoading}
            >
              Forgot password?
            </button>
          )}

          {authError && (
            <p className="auth-error" role="alert">
              {authError}
            </p>
          )}

          {authSuccess && (
            <p role="status" className="auth-success">
              {authSuccess}
            </p>
          )}

          <button
            className="auth-submit"
            type="submit"
            disabled={authLoading}
          >
            {authLoading
              ? "Please wait..."
              : isReset
                ? "Send reset email"
                : isSignUp
                  ? "Create Account"
                  : "Sign In"}
          </button>
        </form>

        <div className="auth-footer">
          {isReset ? (
            <button
              className="auth-text-button"
              type="button"
              onClick={() => changeMode("signin")}
              disabled={authLoading}
            >
              <ArrowLeft size={14} />
              Back to sign in
            </button>
          ) : (
            <p>
              {isSignUp
                ? "Already have an account?"
                : "New to Bushfire AI?"}{" "}
              <button
                className="auth-text-button"
                type="button"
                onClick={() =>
                  changeMode(
                    isSignUp ? "signin" : "signup"
                  )
                }
                disabled={authLoading}
              >
                {isSignUp
                  ? "Sign In"
                  : "Create Account"}
              </button>
            </p>
          )}
        </div>

        <div className="auth-trust">
          <ShieldCheck size={15} />

          <span>
            Secure authentication powered by Firebase.
            Your password is never stored in Bushfire AI's
            database.
          </span>
        </div>
      </section>
    </div>,
    document.body
  );
}