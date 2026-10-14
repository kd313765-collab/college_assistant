import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Assignments() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState("");
  const [sol, setSol] = useState({}); // id -> { busy, text, error }

  useEffect(() => {
    api
      .assignments()
      .then(setItems)
      .catch((e) => setError(e.message));
  }, []);

  async function solve(id) {
    setSol((s) => ({ ...s, [id]: { busy: true } }));
    try {
      const r = await api.solve(id);
      setSol((s) => ({ ...s, [id]: { text: r.solution } }));
    } catch (e) {
      setSol((s) => ({ ...s, [id]: { error: e.message } }));
    }
  }

  async function download(a) {
    try {
      await api.download(a.id, a.file_label);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="page">
      <h2>Assignments</h2>
      {error && <p className="error">{error}</p>}
      {items === null && !error && <p className="muted">Load ho raha hai...</p>}
      {items && items.length === 0 && <p className="muted">Abhi koi assignment post nahi hua hai.</p>}

      {items &&
        items.map((a) => {
          const s = sol[a.id] || {};
          return (
            <article className="card" key={a.id}>
              <div className="card-head">
                <h3>{a.title}</h3>
                <span className="pill">{a.subject_name}</span>
              </div>
              <p className="meta">
                Posted by {a.posted_by} | {a.posted_on} | Last date: {a.due_date} | Max marks: {a.max_marks ?? "-"}
              </p>

              {a.description ? (
                <p className="desc">{a.description}</p>
              ) : (
                <p className="muted">Teacher ne description nahi likhi.</p>
              )}

              <div className="actions">
                {a.has_file && (
                  <button className="secondary" onClick={() => download(a)}>
                    Download: {a.file_label}
                  </button>
                )}
                <button className="primary" onClick={() => solve(a.id)} disabled={s.busy}>
                  {s.busy ? "Solution ban raha hai..." : "Solve karke samjhao"}
                </button>
              </div>

              {s.error && <p className="error">{s.error}</p>}
              {s.text && (
                <div className="solution">
                  <p>{s.text}</p>
                  <small>Pehle khud try karo, phir isse check karo.</small>
                </div>
              )}
            </article>
          );
        })}
    </div>
  );
}
