import type { Metadata } from "next";
import { Notice, PageHeader } from "@/components/ui";
import { type Estimate, type ResultArtifact, results } from "@/lib/data";

export const metadata: Metadata = { title: "Results" };

const fmt = (x: number | undefined) => (typeof x === "number" ? x.toFixed(3) : "–");

function find(name: string): ResultArtifact | undefined {
  return results.artifacts.find((a) => a.name === name);
}

function EstimateRow({ label, e, note }: { label: string; e: Estimate; note?: string }) {
  return (
    <tr>
      <td>{label}</td>
      <td>{fmt(e.estimate)}</td>
      <td>
        [{fmt(e.ci_low)}, {fmt(e.ci_high)}]
      </td>
      <td>{note ?? ""}</td>
    </tr>
  );
}

function Generated() {
  const internal = find("internal_test_analysis");
  const families = find("families_F2_F3_F3b");
  if (!internal) return null;
  const p = internal.payload.primary_HW as Estimate & { supported: boolean };
  const f1 = internal.payload.S1_F1 as Record<string, Estimate & { claim_delta_below_zero: boolean }>;
  return (
    <>
      <h2>Primary endpoint (internal test, arm B, ET)</h2>
      <p>
        Mean within-condition ΔAURC over C4 = {fmt(p.estimate)} (95% patient-group bootstrap CI {fmt(p.ci_low)} to{" "}
        {fmt(p.ci_high)}). H-W is {p.supported ? "supported" : "not supported"} by the pre-registered decision rule
        (CI entirely below 0).
      </p>
      <table>
        <thead>
          <tr>
            <th>Analysis</th>
            <th>Estimate</th>
            <th>95% CI</th>
            <th>Note</th>
          </tr>
        </thead>
        <tbody>
          <EstimateRow label="H-W: mean over C4" e={p} note={p.supported ? "supported" : "not supported"} />
          {Object.entries(f1).map(([c, e]) => (
            <EstimateRow key={c} label={`S1/F1 ${c}`} e={e} note={`Holm p ${fmt(e.holm_p)}`} />
          ))}
        </tbody>
      </table>
      {families ? (
        <>
          <h2>External sets and threshold transfer</h2>
          <ul>
            {Object.entries(families.payload.F2 as Record<string, { estimate: number; holm_p: number }>).map(
              ([ds, v]) => (
                <li key={ds}>
                  {ds}: mean over C4 ΔAURC {fmt(v.estimate)} (Holm p {fmt(v.holm_p)})
                </li>
              ),
            )}
            {Object.entries(
              families.payload.F3_F3b as Record<
                string,
                { delta_risk: number; delta_coverage: number; unsafe_transfer: boolean; inefficient_transfer: boolean }
              >,
            ).map(([ds, v]) => (
              <li key={`t-${ds}`}>
                {ds}: Δrisk {fmt(v.delta_risk)}, Δcoverage {fmt(v.delta_coverage)} —{" "}
                {v.unsafe_transfer ? "unsafe transfer" : "no evidence of unsafe transfer"};{" "}
                {v.inefficient_transfer ? "inefficient transfer" : "no evidence of inefficient transfer"}
              </li>
            ))}
          </ul>
        </>
      ) : null}
      <p className="text-sm">
        Generated from commit {internal.provenance.git_commit.slice(0, 12)} (eval-v1) on {internal.provenance.generated_at}
        . Non-significant results establish neither safety nor equivalence.
      </p>
    </>
  );
}

export default function ResultsPage() {
  return (
    <article className="prose-block">
      <PageHeader title="Results" />
      {results.available ? (
        <>
          <p>
            {results.artifacts.length} provenance-checked result artifact(s) are available in the repository&apos;s
            results index.
          </p>
          <Generated />
        </>
      ) : (
        <Notice>
          <p className="text-lg font-semibold">{results.statement}</p>
        </Notice>
      )}

      <h2>What will be reported</h2>
      <p>
        When the pre-registered analyses have been run, this page shows the following, generated only from
        provenance-stamped result artifacts in the repository:
      </p>
      <ul>
        <li>
          The primary endpoint (mean within-condition ET ΔAURC over C4, internal test, arm B), with its 95%
          patient-group bootstrap CI.
        </li>
        <li>The per-condition components, with −T1c highlighted, and the Full control.</li>
        <li>The external-set estimates, reported separately for each dataset.</li>
        <li>The threshold-transfer quantities.</li>
        <li>The descriptive analyses listed in the protocol.</li>
      </ul>
      <p>Negative and null findings are reported with the same prominence as positive ones.</p>
    </article>
  );
}
