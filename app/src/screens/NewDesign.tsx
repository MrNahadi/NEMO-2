import { Anchor, Ship, Wrench } from "lucide-react";
import { useState } from "react";
import { api, ApiError } from "../api";
import { Dialog } from "../components/Menu";
import { Choicebox, Field, Note } from "../components/ui";
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
    <Dialog
      title="New design"
      description="Each design is saved in its own folder, so it starts fresh and never mixes with another one."
      onClose={onCancel}
      actions={
        <>
          <button className="btn" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={create} disabled={busy}>
            Create design
          </button>
        </>
      }
    >
      <Field label="What should we call this design?">
        <div className="input-wrap">
          <input
            className="input"
            aria-label="Design name"
            placeholder="For example: Engine room generator lift"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !busy && create()}
            autoFocus
          />
        </div>
      </Field>

      <Field label="What are you designing?">
        <Choicebox
          name="new-design-part"
          legend="What are you designing?"
          layout="list"
          value={part}
          onChange={setPart}
          options={PARTS.map((p) => ({
            value: p.id,
            title: p.title,
            description: p.text,
            icon: <p.icon aria-hidden />,
            disabled: !p.ready,
          }))}
        />
      </Field>

      {error && <Note kind="error">{error}</Note>}
    </Dialog>
  );
}
