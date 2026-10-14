import { useState } from "react";
import { api } from "../api.js";

export default function Login({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", roll_no: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function change(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") {
        await api.register(form);
      }
      const data = await api.login(form.email, form.password);
      onLogin(data);
    } catch (err) {
      setError(err.message);
    }
    setBusy(false);
  }

  return (
    <div className="login-page">
      <form className="login-box" onSubmit={submit}>
        <h1>College Assistant</h1>
        <p className="muted">Timetable, result aur assignment, ek hi jagah.</p>

        {mode === "register" && (
          <>
            <label>Name</label>
            <input name="name" value={form.name} onChange={change} required />
            <label>Roll number</label>
            <input name="roll_no" value={form.roll_no} onChange={change} required />
          </>
        )}

        <label>Email</label>
        <input name="email" type="email" value={form.email} onChange={change} required />
        <label>Password</label>
        <input name="password" type="password" value={form.password} onChange={change} required />

        {error && <p className="error">{error}</p>}

        <button className="primary" disabled={busy}>
          {busy ? "Ruko..." : mode === "login" ? "Log in" : "Create account"}
        </button>

        <button
          type="button"
          className="link"
          onClick={() => {
            setMode(mode === "login" ? "register" : "login");
            setError("");
          }}
        >
          {mode === "login" ? "Student ho? Naya account banao" : "Account hai? Log in karo"}
        </button>

        <p className="demo">
          Demo: student@college.test / student123
          <br />
          teacher@college.test / teacher123
        </p>
      </form>
    </div>
  );
}
