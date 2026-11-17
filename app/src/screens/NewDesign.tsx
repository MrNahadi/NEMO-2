import { Anchor, Ship, Wrench } from "lucide-react";
import { useState } from "react";
import { api, ApiError } from "../api";
import { Banner, Field } from "../components/ui";
import type { Project } from "../types";

const PARTS = [
  { id: "padeye", title: "Lifting padeye", text: "A plate with a hole for a shackle, welded to a deck or structure for lifting.", icon: Anchor, ready: true },
  { id: "pipe-bracket", title: "Pipe support bracket", text: "A seat plate with two knees, welded to a bulkhead, holding a pipe with a U-bolt. Checks the pipe span for vibration too.", icon: Wrench, ready: true },
  { id: "stabilizer", title: "Stabilizer fin", text: "The skin, spars, ribs and stock inside a roll-stabilizer fin, from the foil loads at full speed.", icon: Ship, ready: true },
];

export function NewDesign({ onCreated, onCancel }: { onCreated: (p: Project) => void; onCancel: () => void }) {
  const [name, setName] = useState("");
  const [part, setPart] = useState("padeye");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function create() {
    setBusy(true);
    setError(null);
    try {
      onCreated(await api.createProject(name.trim() || "Untitled design", part));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
      setBusy(false);
    }
  }

  return (
    <div className="page page-narrow">
      <h1 className="title">New design</h1>
      <p className="lead">Each design is saved in its own folder, so it starts fresh and never mixes with another one.</p>

      <div className="form mt-6">
        <Field label="What should we call this design?">
          <div className="input-wrap name-input">
            <input
              className="input"
              aria-label="Design name"
              placeholder="For example: Engine room generator lift"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && create()}
              autoFocus
            />
          </div>
        </Field>

        <Field label="What are you designing?">
          <div className="part-grid">
            {PARTS.map((p) => (
              <button
                key={p.id}
                className="card choice-card"
                aria-pressed={part === p.id}
                disabled={!p.ready}
                onClick={() => setPart(p.id)}
              >
                <span className="icon">
                  <p.icon size={20} aria-hidden />
                </span>
                <span className="choice-name">{p.title}</span>
                <span className="caption">{p.text}</span>
              </button>
            ))}
          </div>
        </Field>

        {error && <Banner kind="error">{error}</Banner>}
        <div className="actions">
          <button className="btn btn-primary" onClick={create} disabled={busy}>
            Create design
          </button>
          <button className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
