import { useState } from "react";
import {
  Mail,
  Send,
  UserRound,
  MessageSquare,
  ExternalLink,
  ShieldCheck,
  Code2,
} from "lucide-react";

import "./Contact.css";

const initialForm = {
  name: "",
  email: "",
  subject: "General Enquiry",
  message: "",
};

export default function Contact() {
  const [form, setForm] = useState(initialForm);
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (sending) return;

    setSending(true);
    setStatus(null);

    try {
      const response = await fetch(
        "https://formspree.io/f/moejkrad",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
          },
          body: JSON.stringify(form),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.errors?.[0]?.message ||
          "Unable to send your message. Please try again."
        );
      }

      setForm(initialForm);
      setStatus({
        type: "success",
        message: "Message sent successfully! Thank you for getting in touch.",
      });
    } catch (error) {
      setStatus({
        type: "error",
        message: error.message || "Something went wrong. Please try again.",
      });
    } finally {
      setSending(false);
    }
  };

  const updateField = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  return (
    <div className="contact-page">
      <div className="contact-heading">
        <span className="contact-eyebrow">GET IN TOUCH</span>
        <h1>Contact Developer</h1>
        <p>
          Have a question, suggestion, or collaboration idea?
          I'd love to hear from you.
        </p>
      </div>

      <div className="contact-grid">
        <section className="contact-card contact-form-card">
          <div className="contact-card-heading">
            <div className="contact-icon-box">
              <Mail size={21} />
            </div>

            <div>
              <h2>Send a Message</h2>
              <p>Share your feedback or get in touch.</p>
            </div>
          </div>

          <form className="contact-form" onSubmit={handleSubmit}>
            <div className="contact-form-row">
              <label>
                Full Name
                <div className="contact-input-wrap">
                  <UserRound size={17} />
                  <input
                    name="name"
                    value={form.name}
                    onChange={updateField}
                    placeholder="Your full name"
                    autoComplete="name"
                    maxLength={100}
                    required
                  />
                </div>
              </label>

              <label>
                Email Address
                <div className="contact-input-wrap">
                  <Mail size={17} />
                  <input
                    type="email"
                    name="email"
                    value={form.email}
                    onChange={updateField}
                    placeholder="you@example.com"
                    autoComplete="email"
                    maxLength={254}
                    required
                  />
                </div>
              </label>
            </div>

            <label>
              Subject
              <select
                name="subject"
                value={form.subject}
                onChange={updateField}
              >
                <option>General Enquiry</option>
                <option>Bug Report</option>
                <option>Project Feedback</option>
                <option>Collaboration</option>
              </select>
            </label>

            <label>
              Your Message
              <div className="contact-textarea-wrap">
                <MessageSquare size={17} />
                <textarea
                  name="message"
                  value={form.message}
                  onChange={updateField}
                  placeholder="Tell me what's on your mind..."
                  rows={7}
                  minLength={10}
                  maxLength={3000}
                  required
                />
              </div>
            </label>

            <button
              className="contact-submit"
              type="submit"
              disabled={sending}
            >
              <Send size={17} />
              {sending ? "Sending..." : "Send Message"}
            </button>

            {status && (
              <p
                className={`contact-status contact-status-${status.type}`}
                role="status"
              >
                {status.message}
              </p>
            )}

            <p className="contact-form-note">
              Messages are processed through Formspree.
              Your email address is used only to respond to your enquiry.
            </p>
          </form>
        </section>

        <aside className="contact-profile-column">
          <section className="contact-card contact-profile-card">
          <img
  src="/developer-profile.jpg"
  alt="Ayub Gurung"
  className="contact-avatar-photo"
/>

            <span className="contact-profile-label">
              MEET THE DEVELOPER
            </span>

            <h2>Ayub Gurung</h2>

            <p className="contact-role">
              Information Technology Student
            </p>

            <p className="contact-bio">
              Interested in full-stack development,
              machine learning, and building practical
              technology solutions to real-world problems.
            </p>

            <div className="contact-social-links">
              <a
                href="https://www.linkedin.com/in/ayubg"
                target="_blank"
                rel="noopener noreferrer"
              >
                LinkedIn
                <ExternalLink size={15} />
              </a>

              <a
                href="https://github.com/Ayu-gu"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub
                <ExternalLink size={15} />
              </a>
            </div>
          </section>

          <section className="contact-card contact-privacy-card">
            <ShieldCheck size={21} />

            <div>
              <h3>Private & Direct</h3>
              <p>
                Messages will be sent securely through
                the platform. Your contact details
                won't be displayed publicly.
              </p>
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
