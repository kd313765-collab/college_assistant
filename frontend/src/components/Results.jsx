import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Results() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [subject, setSubject] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    api
      .results()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="page"><p className="error">{error}</p></div>;
  if (!data) return <div className="page"><p className="muted">Load ho raha hai...</p></div>;
  if (data.rows.length === 0) {
    return (
      <div className="page">
        <h2>Results</h2>
        <p className="muted">Abhi koi result upload nahi hua. Teacher panel mein CSV upload karo.</p>
      </div>
    );
  }

  const rows = data.rows.filter((r) => (!subject || r.subject_code === subject) && (!status || r.status === status));

  return (
    <div className="page">
      <h2>Results</h2>

      <div className="card">
        <h3>Subject ke hisaab se</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Subject</th>
                <th>Students</th>
                <th>Pass</th>
                <th>Fail</th>
                <th>Topper</th>
              </tr>
            </thead>
            <tbody>
              {data.summary.map((s) => (
                <tr key={s.subject_code}>
                  <td>{s.subject_name}</td>
                  <td>{s.students}</td>
                  <td>{s.passed}</td>
                  <td>{s.failed}</td>
                  <td>
                    {s.topper} ({s.topper_percent}%)
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h3>Poori class ke top 3</h3>
        <ol className="plain">
          {data.overall_top.map((t) => (
            <li key={t.roll_no}>
              {t.student_name} ({t.roll_no}): {t.total}/{t.out_of} ({t.percent}%)
            </li>
          ))}
        </ol>
      </div>

      <div className="card">
        <h3>Sabke marks</h3>
        <div className="row">
          <div>
            <label>Subject</label>
            <select value={subject} onChange={(e) => setSubject(e.target.value)}>
              <option value="">Sab</option>
              {data.summary.map((s) => (
                <option key={s.subject_code} value={s.subject_code}>
                  {s.subject_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Sab</option>
              <option value="pass">Pass</option>
              <option value="fail">Fail</option>
            </select>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Roll no</th>
                <th>Name</th>
                <th>Subject</th>
                <th>Marks</th>
                <th>%</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  <td>{r.roll_no}</td>
                  <td>{r.student_name}</td>
                  <td>{r.subject_name}</td>
                  <td>
                    {r.marks}/{r.max_marks}
                  </td>
                  <td>{r.percent}</td>
                  <td className={r.status === "fail" ? "st-fail" : "st-pass"}>{r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted">{rows.length} rows</p>
      </div>
    </div>
  );
}
