import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { ArrowLeft, LockKeyhole, Mail, ShieldCheck, X } from "lucide-react";
import { signInWithPopup } from "firebase/auth";
import { auth, googleProvider } from "../firebase";
import "./AuthModal.css";

export default function AuthModal({ isOpen, onClose }) {
  const [mode, setMode] = useState("signin");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");

  const handleGoogleSignIn = async () => {
    setAuthLoading(true);
    setAuthError("");

    try {
      await signInWithPopup(auth, googleProvider);
      onClose();
    } catch (error) {
      if (error.code !== "auth/popup-closed-by-user") {
        console.error("Google sign-in failed:", error.code);
        setAuthError(
          error.code === "auth/unauthorized-domain"
            ? "This website is not authorised in Firebase Authentication."
            : "Google sign-in failed. Please try again."
        );
      }
    } finally {
      setAuthLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (event) => {
      if (event.key === "Escape") onClose();
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const isSignUp = mode === "signup";
  const isReset = mode === "reset";

  const handleSubmit = (event) => {
    event.preventDefault();
  };

  return createPortal(
    <div
      className="auth-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
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
          aria-label="Close sign in"
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
              ? "Enter your email to reset your password."
              : isSignUp
                ? "Save locations and keep your bushfire risk assessments together."
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
              {authLoading ? "Connecting to Google..." : "Continue with Google"}
            </button>

            {authError && (
              <p className="auth-error" role="alert">
                {authError}
              </p>
            )}

            <div className="auth-divider">
              <span>or continue with email</span>
            </div>
          </>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="auth-email">Email address</label>
          <div className="auth-input-wrap">
            <Mail size={17} />
            <input
              id="auth-email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
          </div>

          {!isReset && (
            <>
              <label htmlFor="auth-password">Password</label>
              <div className="auth-input-wrap">
                <LockKeyhole size={17} />
                <input
                  id="auth-password"
                  type="password"
                  placeholder="Enter your password"
                  autoComplete={isSignUp ? "new-password" : "current-password"}
                  minLength={6}
                  required
                />
              </div>
            </>
          )}

          {!isSignUp && !isReset && (
            <button
              className="auth-text-button auth-forgot"
              type="button"
              onClick={() => setMode("reset")}
            >
              Forgot password?
            </button>
          )}

          <button className="auth-submit" type="submit" disabled>
            {isReset
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
              onClick={() => setMode("signin")}
            >
              <ArrowLeft size={14} /> Back to sign in
            </button>
          ) : (
            <p>
              {isSignUp ? "Already have an account?" : "New to Bushfire AI?"}{" "}
              <button
                className="auth-text-button"
                type="button"
                onClick={() => setMode(isSignUp ? "signin" : "signup")}
              >
                {isSignUp ? "Sign In" : "Create Account"}
              </button>
            </p>
          )}
        </div>

        <div className="auth-trust">
          <ShieldCheck size={15} />
          <span>
            Authentication setup in progress. Sign-in will be enabled
            when Firebase is connected.
          </span>
        </div>
      </section>
    </div>,
    document.body
  );
}
