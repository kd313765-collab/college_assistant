import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Notifications() {
  const [list, setList] = useState([]);
  const [open, setOpen] = useState(false);

  async function load() {
    try {
      setList(await api.notifications());
    } catch {
      // chup raho, agli baar try karenge
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 60000);
    return () => clearInterval(t);
  }, []);

  const unread = list.filter((n) => !n.is_read).length;

  async function toggle() {
    const willOpen = !open;
    setOpen(willOpen);
    if (willOpen && unread > 0) {
      await api.markRead();
      // list mein turant read dikhane ke liye thoda delay
      setTimeout(load, 1500);
    }
  }

  return (
    <div className="notif">
      <button className="link" onClick={toggle}>
        Reminders{unread > 0 && <span className="count">{unread}</span>}
      </button>
      {open && (
        <div className="notif-list">
          {list.length === 0 && <p className="muted">Abhi koi reminder nahi hai.</p>}
          {list.map((n) => (
            <div key={n.id} className={"note" + (n.is_read ? "" : " new")}>
              <p>{n.message}</p>
              <small>{n.created_on}</small>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
