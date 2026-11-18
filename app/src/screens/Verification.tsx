import { ChevronRight, Loader2, Play } from "lucide-react";
import { Fragment, useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { Formula, Working } from "../components/Formula";
import { Page, PageHeader } from "../components/Page";
import { Note, Progress, Skeleton, Status } from "../components/ui";
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
  const loading = listed.length === 0 && !error;

  const lastRun = busy
    ? null
    : latest
      ? `Last run ${new Date(latest.ran_at).toLocaleString()} with NEMO ${latest.nemo_version}: ${
          latest.passed ? "every benchmark passed." : "one or more benchmarks failed."
        }`
      : loading
        ? null
        : "Not run on this computer yet. It takes about half a minute.";

  return (
    <Page>
      <PageHeader
        title="Verification"
        description={
          <span className="v-desc">
            <span className="v-desc-body">
              NEMO is checked against problems whose answers are known from theory or were worked out by hand. Run them here to see
              NEMO's calculation engine and stress solver reproduce those answers on this computer.
            </span>
            {lastRun && <span className="v-last-run">{lastRun}</span>}
          </span>
        }
        actions={
          <button className="btn btn-primary" onClick={runNow} disabled={busy}>
            {busy ? <Loader2 className="spin" aria-hidden /> : <Play aria-hidden />}
            {busy ? `Running ${done + 1} of ${listed.length}` : "Run verification"}
          </button>
        }
      />

      {busy && (
        <div className="v-progress">
          <Progress value={done} max={Math.max(listed.length, 1)} label="Benchmarks finished" />
        </div>
      )}
      {error && (
        <div className="v-error">
          <Note kind="error">{error}</Note>
        </div>
      )}

      <div className="table-wrap">
        <table className="table v-table">
          <thead>
            <tr>
              <th>Benchmark</th>
              <th>Reference</th>
              <th className="result">Result</th>
              <th className="v-chev">
                <span className="sr-only">Show detail</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {loading &&
              [0, 1, 2].map((i) => (
                <tr key={i} aria-hidden>
                  <td className="name">
                    <div className="stack gap-2">
                      <Skeleton width={220} height={16} />
                      <Skeleton width={340} height={14} />
                    </div>
                  </td>
                  <td>
                    <Skeleton width={160} height={14} />
                  </td>
                  <td>
                    <Skeleton width={72} height={14} />
                  </td>
                  <td className="v-chev" />
                </tr>
              ))}
            {listed.map((b) => {
              const r = resultFor(b.id);
              const isRunning = running === b.id;
              const expanded = open === b.id && !!r;
              return (
                <Fragment key={b.id}>
                  <tr className={r ? `row-link${expanded ? " open" : ""}` : undefined} onClick={() => r && setOpen(expanded ? null : b.id)}>
                    <td className="name cell-truncate">
                      <button
                        type="button"
                        className="v-bench"
                        aria-expanded={expanded}
                        disabled={!r}
                        onClick={(e) => {
                          e.stopPropagation();
                          if (r) setOpen(expanded ? null : b.id);
                        }}
                      >
                        <span className="v-bench-title">{b.title}</span>
                        <span className="v-bench-desc">{b.description}</span>
                      </button>
                    </td>
                    <td className="ref">
                      <span className="v-ref">{b.source}</span>
                    </td>
                    <td className="result">
                      {isRunning ? (
                        <Status tone="gray">
                          <span className="text-secondary">Running</span>
                        </Status>
                      ) : r ? (
                        r.passed ? (
                          <Status tone="green">Pass</Status>
                        ) : (
                          <Status tone="red">Fail</Status>
                        )
                      ) : (
                        <Status tone="gray">
                          <span className="text-secondary">Not run</span>
                        </Status>
                      )}
                    </td>
                    <td className="v-chev">{r && <ChevronRight aria-hidden className="bench-chevron" />}</td>
                  </tr>
                  {expanded && r && (
                    <tr className="v-detail">
                      <td colSpan={4} className="v-detail-cell">
                        <div className="v-detail-body">
                          {r.error && <Note kind="error">{r.error}</Note>}
                          <ComparisonTable rows={r.comparisons} />
                          <div className="stack gap-2">
                            <h3 className="text-heading-14">How the reference answer is worked out</h3>
                            <Working steps={r.setup.filter((s) => s.value !== 0)} />
                            {r.setup
                              .filter((s) => s.value === 0)
                              .map((s, i) => (
                                <p key={i} className="caption">
                                  <b>{s.label}:</b> <Formula text={`${s.formula}. ${s.substituted}`} />
                                </p>
                              ))}
                            {r.mesh && (
                              <p className="caption">
                                Mesh: {r.mesh.elements.toLocaleString()} elements, {r.mesh.equations.toLocaleString()} equations. Took{" "}
                                {r.seconds.toFixed(1)} s.
                              </p>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </Page>
  );
}

function ComparisonTable({ rows }: { rows: Comparison[] }) {
  const fmt = (v: number) => (Math.abs(v) >= 1000 ? v.toLocaleString(undefined, { maximumFractionDigits: 1 }) : v.toLocaleString(undefined, { maximumSignificantDigits: 6 }));
  return (
    <div className="table-wrap">
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
    </div>
  );
}
