import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

const AGENT_LABEL = {
  result: "Result agent",
  timetable: "Timetable agent",
  assignment: "Assignment agent",
  other: "Task manager",
};

const CHIPS = {
  student: ["Aaj kaun kaun si class hai?", "Mere marks kitne aaye?", "Koi naya assignment aaya?", "DAA mein abhi kaunsa topic chal raha hai?"],
  teacher: ["Kitne students fail hue?", "DBMS ke top 3 students", "Kal ka timetable batao", "Assignment 3 solve karo"],
};

function Table({ rows }) {
  if (!rows || rows.length === 0) return null;
  const cols = Object.keys(rows[0]);
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c}>{c.replace(/_/g, " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c}>{String(r[c] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Chat({ user }) {
  const [messages, setMessages] = useState([
    { from: "bot", agent: "other", text: "Namaste " + user.name.split(" ")[0] + "! Kya poochna hai?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [speak, setSpeak] = useState(false);
  const [recording, setRecording] = useState(false);

  const recorder = useRef(null);
  const chunks = useRef([]);
  const bottom = useRef(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    setInput("");
    setMessages((m) => [...m, { from: "user", text: msg }]);
    setLoading(true);

    try {
      const data = await api.chat(msg);
      setMessages((m) => [...m, { from: "bot", agent: data.agent, text: data.answer, rows: data.rows }]);
      if (speak) playVoice(data.answer);
    } catch (err) {
      setMessages((m) => [...m, { from: "bot", agent: "other", text: err.message, isError: true }]);
    }
    setLoading(false);
  }

  async function playVoice(text) {
    try {
      const blob = await api.textToSpeech(text);
      new Audio(URL.createObjectURL(blob)).play();
    } catch {
      // voice nahi chali to koi baat nahi, text to hai hi
    }
  }

  async function toggleMic() {
    if (recording) {
      recorder.current.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const rec = new MediaRecorder(stream);
      chunks.current = [];
      rec.ondataavailable = (e) => chunks.current.push(e.data);
      rec.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setRecording(false);
        try {
          const { text } = await api.speechToText(new Blob(chunks.current, { type: "audio/webm" }));
          if (text) send(text);
        } catch (err) {
          setMessages((m) => [...m, { from: "bot", agent: "other", text: err.message, isError: true }]);
        }
      };
      rec.start();
      recorder.current = rec;
      setRecording(true);
    } catch {
      alert("Mic ki permission do");
    }
  }

  return (
    <div className="chat">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={"msg " + m.from}>
            {m.from === "bot" && m.agent && <span className={"tag " + m.agent}>{AGENT_LABEL[m.agent]}</span>}
            <div className={"bubble" + (m.isError ? " err" : "")}>
              <p>{m.text}</p>
              <Table rows={m.rows} />
            </div>
          </div>
        ))}
        {loading && (
          <div className="msg bot">
            <div className="bubble typing">Soch raha hoon...</div>
          </div>
        )}
        <div ref={bottom} />
      </div>

      <div className="chips">
        {CHIPS[user.role].map((c) => (
          <button key={c} className="chip" onClick={() => send(c)}>
            {c}
          </button>
        ))}
      </div>

      <div className="inputbar">
        <button
          className={"icon" + (recording ? " rec" : "")}
          onClick={toggleMic}
          title="Bolke poochho"
          aria-label={recording ? "Recording rok do" : "Bolke poochho"}
        >
          {recording ? "Stop" : "Mic"}
        </button>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Apna sawal likho..."
        />
        <button className="primary" onClick={() => send()} disabled={loading}>
          Send
        </button>
        <label className="speak">
          <input type="checkbox" checked={speak} onChange={(e) => setSpeak(e.target.checked)} />
          Jawab bolke sunao
        </label>
      </div>
    </div>
  );
}
