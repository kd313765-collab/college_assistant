import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function TeacherPanel() {
  const [subjects, setSubjects] = useState([]);
  const [msg, setMsg] = useState("");

  const [resultFile, setResultFile] = useState(null);
  const [a, setA] = useState({ subject_code: "", title: "", description: "", due_date: "", max_marks: 10 });
  const [aFile, setAFile] = useState(null);
  const [t, setT] = useState({ subject_code: "", unit: "", topic: "" });
  const [topics, setTopics] = useState([]);

  function loadTopics() {
    api.topics().then(setTopics).catch(() => {});
  }

  useEffect(() => {
    api.subjects().then(setSubjects).catch(() => {});
    loadTopics();
  }, []);

  function say(text) {
    setMsg(text);
    setTimeout(() => setMsg(""), 5000);
  }

  async function uploadResults(e) {
    e.preventDefault();
    if (!resultFile) return say("Pehle file chuno");
    try {
      const r = await api.uploadResults(resultFile);
      say(r.rows + " rows upload ho gayi");
    } catch (err) {
      say(err.message);
    }
  }

  async function postAssignment(e) {
    e.preventDefault();
    const fd = new FormData();
    Object.entries(a).forEach(([k, v]) => fd.append(k, v));
    if (aFile) fd.append("file", aFile);
    try {
      await api.postAssignment(fd);
      say("Assignment post ho gaya, students ko reminder chala gaya");
      setA({ subject_code: "", title: "", description: "", due_date: "", max_marks: 10 });
      setAFile(null);
    } catch (err) {
      say(err.message);
    }
  }

  async function saveTopic(e) {
    e.preventDefault();
    try {
      await api.setTopic(t);
      say("Topic update ho gaya");
      setT({ subject_code: "", unit: "", topic: "" });
      loadTopics();
    } catch (err) {
      say(err.message);
    }
  }

  const subjectSelect = (value, onChange) => (
    <select value={value} onChange={onChange} required>
      <option value="">Subject chuno</option>
      {subjects.map((s) => (
        <option key={s.subject_code} value={s.subject_code}>
          {s.subject_name} ({s.subject_code})
        </option>
      ))}
    </select>
  );

  return (
    <div className="panel">
      {msg && <div className="toast">{msg}</div>}

      <form className="card" onSubmit={uploadResults}>
        <h2>Result upload karo</h2>
        <p className="muted">
          CSV ya Excel. Columns: roll_no, student_name, subject_code, subject_name, marks, max_marks
        </p>
        <input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => setResultFile(e.target.files[0])} />
        <button className="primary">Upload</button>
      </form>

      <form className="card" onSubmit={postAssignment}>
        <h2>Assignment post karo</h2>
        {subjectSelect(a.subject_code, (e) => setA({ ...a, subject_code: e.target.value }))}
        <input placeholder="Title (jaise DAA Assignment-4)" value={a.title} onChange={(e) => setA({ ...a, title: e.target.value })} required />
        <textarea placeholder="Description / questions" rows={4} value={a.description} onChange={(e) => setA({ ...a, description: e.target.value })} />
        <div className="row">
          <div>
            <label>Last date</label>
            <input type="date" value={a.due_date} onChange={(e) => setA({ ...a, due_date: e.target.value })} />
          </div>
          <div>
            <label>Max marks</label>
            <input type="number" value={a.max_marks} onChange={(e) => setA({ ...a, max_marks: e.target.value })} />
          </div>
        </div>
        <input type="file" accept=".pdf,.txt,.doc,.docx" onChange={(e) => setAFile(e.target.files[0])} />
        <button className="primary">Post assignment</button>
      </form>

      <form className="card" onSubmit={saveTopic}>
        <h2>Abhi kaunsa topic chal raha hai</h2>
        {subjectSelect(t.subject_code, (e) => setT({ ...t, subject_code: e.target.value }))}
        <input placeholder="Unit (jaise 3)" value={t.unit} onChange={(e) => setT({ ...t, unit: e.target.value })} />
        <input placeholder="Topic" value={t.topic} onChange={(e) => setT({ ...t, topic: e.target.value })} required />
        <button className="primary">Save topic</button>

        {topics.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Subject</th>
                  <th>Unit</th>
                  <th>Topic</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {topics.map((x) => (
                  <tr key={x.subject_code}>
                    <td>{x.subject_name}</td>
                    <td>{x.unit}</td>
                    <td>{x.topic}</td>
                    <td>{x.updated_on}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </form>
    </div>
  );
}
