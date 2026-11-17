import { Loader2, Play } from "lucide-react";
import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { Formula, Working } from "../components/Formula";
import { Banner } from "../components/ui";
import type { Benchmark, Comparison, VerificationResult } from "../types";

interface Listed {
  id: string;
  title: string;
  description: string;
  source: string;
}

export function Verification() {
  const [listed, setListed] = useState<Listed[]>([]);
  const [latest, setLatest] = useState<VerificationResult | null>(null);
  const [live, setLive] = useState<Record<string, Benchmark>>({});
  const [running, setRunning] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    api.verification().then((v) => {
      setListed(v.benchmarks);
      setLatest(v.latest);
    }).catch((e) => setError(e instanceof ApiError ? e.message : String(e)));
  }, []);

  async function runNow() {
    setBusy(true);
    setError(null);
    setLive({});
    try {
      const start = await api.startVerification();
      let next = 0;
      for (;;) {
        const s = await api.runStatus(start.id, next);
        next = s.next;
        for (const e of s.events) {
          if (e.kind === "benchmark_start") setRunning(e.id);
          if (e.kind === "benchmark_done") setLive((prev) => ({ ...prev, [e.id]: e as unknown as Benchmark }));
        }
        if (s.state === "done") {
          if (s.result) setLatest(s.result);
          break;
        }
        if (s.state === "failed") throw new ApiError(s.error ?? "Verification failed.");
        await new Promise((r) => setTimeout(r, 400));
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
      setRunning(null);
    }
  }

  const resultFor = (id: string): Benchmark | undefined => live[id] ?? (busy ? undefined : latest?.benchmarks.find((b) => b.id === id));
  const done = Object.keys(live).length;

  return (
    <div className="page page-wide">
      <h1 className="title">Verification</h1>
      <p className="lead">
        NEMO is checked against problems whose answers are known from theory or were worked out by hand. Run them here to see
        NEMO's calculation engine and stress solver reproduce those answers on this computer.
      </p>
      <div className="actions" style={{ marginTop: 32 }}>
        <button className="btn btn-primary" onClick={runNow} disabled={busy}>
          {busy ? <Loader2 className="spin" aria-hidden /> : <Play aria-hidden />}
          {busy ? `Running ${done + 1} of ${listed.length}` : "Run verification now"}
        </button>
        {latest && !busy && (
          <span className="caption">
            Last run {new Date(latest.ran_at).toLocaleString()} with NEMO {latest.nemo_version}:{" "}
            {latest.passed ? "every benchmark passed." : "one or more benchmarks failed."}
          </span>
        )}
        {!latest && !busy && <span className="caption">Not run on this computer yet. It takes about half a minute.</span>}
      </div>
      {error && <div className="mt-3"><Banner kind="error">{error}</Banner></div>}

      <div className="bench-list mt-6">
        {listed.map((b) => {
          const r = resultFor(b.id);
          const isRunning = running === b.id;
          const expanded = open === b.id;
          return (
            <article key={b.id} className="bench">
              <button type="button" className="bench-head" aria-expanded={expanded} onClick={() => setOpen(expanded ? null : b.id)} disabled={!r}>
                <span className="stack">
                  <span className="bench-title">{b.title}</span>
                  <span className="caption">{b.description} Reference: {b.source}.</span>
                </span>
                <span className="bench-state">
                  {isRunning ? (
                    <span className="badge badge-neutral"><Loader2 className="spin" aria-hidden /> Running</span>
                  ) : r ? (
                    <span className={`badge ${r.passed ? "badge-pass" : "badge-fail"}`}>{r.passed ? "Pass" : "Fail"}</span>
                  ) : (
                    <span className="badge badge-neutral">Not run</span>
                  )}
                </span>
              </button>
              {r && (
                <div className="bench-body">
                  {r.error && <Banner kind="error">{r.error}</Banner>}
                  <ComparisonTable rows={r.comparisons} />
                  {expanded && (
                    <div className="stack gap-2 mt-3">
                      <h3 className="view-heading">How the reference answer is worked out</h3>
                      <Working steps={r.setup.filter((s) => s.value !== 0)} />
                      {r.setup.filter((s) => s.value === 0).map((s, i) => (
                        <p key={i} className="caption"><b>{s.label}:</b> <Formula text={`${s.formula}. ${s.substituted}`} /></p>
                      ))}
                      {r.mesh && <p className="caption">Mesh: {r.mesh.elements.toLocaleString()} elements, {r.mesh.equations.toLocaleString()} equations. Took {r.seconds.toFixed(1)} s.</p>}
                    </div>
                  )}
                  {!expanded && <button type="button" className="link" onClick={() => setOpen(b.id)}>Show how the reference is worked out</button>}
                </div>
              )}
            </article>
          );
        })}
      </div>
    </div>
  );
}

function ComparisonTable({ rows }: { rows: Comparison[] }) {
  const fmt = (v: number) => (Math.abs(v) >= 1000 ? v.toLocaleString(undefined, { maximumFractionDigits: 1 }) : v.toLocaleString(undefined, { maximumSignificantDigits: 6 }));
  return (
    <table className="data">
      <thead>
        <tr><th>Quantity</th><th className="r">Known answer</th><th className="r">NEMO</th><th className="r">Difference</th><th className="r">Allowed</th><th className="r">Result</th></tr>
      </thead>
      <tbody>
        {rows.map((c) => (
          <tr key={c.quantity}>
            <td><Formula text={c.quantity} /></td>
            <td className="r">{fmt(c.reference)} {c.unit}</td>
            <td className="r">{fmt(c.nemo)} {c.unit}</td>
            <td className="r">{Math.abs(c.error_percent) < 0.0005 ? "0.000%" : `${c.error_percent > 0 ? "+" : ""}${c.error_percent.toFixed(3)}%`}</td>
            <td className="r">±{c.tolerance_percent < 0.001 ? "0.000001" : c.tolerance_percent}%</td>
            <td className="r">{c.passed ? <span className="text-pass">Pass</span> : <span className="text-fail">Fail</span>}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
