import Link from "next/link";
import { Timeline } from "@/components/Gates";
import { StageOverview } from "@/components/Overview";
import { Card, Notice, StatusBadge } from "@/components/ui";
import { derivedFacts, experiments, gateCounts, results, status } from "@/lib/data";

export default function HomePage() {
  const groups = ["A", "B", "C", "D"];
  return (
    <div>
      <section className="mb-10">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <StatusBadge status={status.protocol.status} />
          <span className="text-sm text-slate-500">
            Protocol {status.protocol.version}, frozen {status.protocol.frozen_on}
          </span>
        </div>
        <h1 className="font-serif text-3xl font-semibold leading-tight tracking-tight text-slate-900 sm:text-4xl dark:text-slate-50">
          {status.project.title}
        </h1>
        <p className="mt-2 text-slate-500">{status.project.type}</p>
        <p className="mt-6 text-lg font-medium text-slate-900 dark:text-slate-100">{status.headline}</p>
      </section>

      <Notice>
        {results.available ? null : <strong>No results exist. </strong>}
        {results.statement} {derivedFacts().join(" ")}
      </Notice>

      <section className="my-10">
        <h2 className="mb-3 font-serif text-2xl font-semibold text-slate-900 dark:text-slate-50">Current status</h2>
        <StageOverview />
        <p className="mt-3 text-sm text-slate-500">
          Data authorization: {status.data.authorization.toLowerCase()}
          {status.data.authorization_basis === "OWNER_APPROVED_ALTERNATIVE"
            ? " (owner-approved alternative; no external TCIA authorization is claimed)"
            : ""}
          . Data acquired:{" "}
          {status.data.acquired ? "yes" : "no"}. {status.data.statement}
        </p>
      </section>

      <section className="my-10">
        <h2 className="mb-3 font-serif text-2xl font-semibold text-slate-900 dark:text-slate-50">Central question</h2>
        <blockquote className="border-l-4 border-slate-300 pl-4 text-lg italic text-slate-700 dark:border-slate-700 dark:text-slate-300">
          {status.project.central_question}
        </blockquote>
        <p className="mt-4">
          <Link href="/research/" className="text-blue-700 underline dark:text-blue-400">
            Research question and hypotheses
          </Link>
        </p>
      </section>

      <section className="my-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {groups.map((g) => {
          const c = gateCounts(g);
          return (
            <Card key={g} title={`Gates ${g}`}>
              <p className="text-2xl font-semibold">
                {c.closed} / {c.total}
              </p>
              <p className="text-sm text-slate-500">closed or owner-waived</p>
              <p className="mt-2 text-sm">{status.gate_groups[g]}</p>
            </Card>
          );
        })}
      </section>

      {status.next_step ? (
        <section className="my-10">
          <h2 className="mb-3 font-serif text-2xl font-semibold text-slate-900 dark:text-slate-50">Next step</h2>
          <p>
            <span className="mono">{status.next_step.gate}</span>. {status.next_step.description}
          </p>
        </section>
      ) : null}

      <section className="my-10">
        <h2 className="mb-3 font-serif text-2xl font-semibold text-slate-900 dark:text-slate-50">Experiments</h2>
        <ul className="space-y-2">
          {experiments.map((e) => (
            <li key={e.id} className="flex flex-wrap items-center gap-2">
              <span className="font-mono">{e.id}</span>
              <StatusBadge status={e.status} />
              <span>{e.title}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="my-10">
        <h2 className="mb-3 font-serif text-2xl font-semibold text-slate-900 dark:text-slate-50">Research timeline</h2>
        <Timeline />
      </section>
    </div>
  );
}
