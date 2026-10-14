import { useState } from "react";
import Login from "./components/Login.jsx";
import Chat from "./components/Chat.jsx";
import Assignments from "./components/Assignments.jsx";
import Results from "./components/Results.jsx";
import TeacherPanel from "./components/TeacherPanel.jsx";
import Notifications from "./components/Notifications.jsx";

export default function App() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("user"));
    } catch {
      return null;
    }
  });
  const [tab, setTab] = useState("chat");

  function onLogin(data) {
    localStorage.setItem("token", data.token);
    localStorage.setItem("user", JSON.stringify(data.user));
    setUser(data.user);
  }

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    setTab("chat");
  }

  if (!user) return <Login onLogin={onLogin} />;

  const isTeacher = user.role === "teacher";

  const tabs = [
    { id: "chat", label: "Chat" },
    { id: "assignments", label: "Assignments" },
    ...(isTeacher
      ? [
          { id: "results", label: "Results" },
          { id: "panel", label: "Teacher panel" },
        ]
      : []),
  ];

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <h1>College Assistant</h1>
          <span className="who">
            {user.name} ({user.role})
          </span>
        </div>

        <nav className="tabs">
          {tabs.map((t) => (
            <button key={t.id} className={tab === t.id ? "tab on" : "tab"} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>

        <div className="right">
          {!isTeacher && <Notifications />}
          <button className="link" onClick={logout}>
            Log out
          </button>
        </div>
      </header>

      <main className="main">
        {tab === "chat" && <Chat user={user} />}
        {tab === "assignments" && <Assignments />}
        {tab === "results" && isTeacher && <Results />}
        {tab === "panel" && isTeacher && <TeacherPanel />}
      </main>
    </div>
  );
}
