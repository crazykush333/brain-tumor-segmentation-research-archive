import type { Metadata } from "next";
import { Notice, PageHeader } from "@/components/ui";
import { results } from "@/lib/data";

export const metadata: Metadata = { title: "Results" };

export default function ResultsPage() {
  return (
    <article className="prose-block">
      <PageHeader title="Results" />
      {results.available ? (
        <p>
          {results.artifacts.length} provenance-checked result artifact(s) are available in the repository&apos;s
          results index.
        </p>
      ) : (
        <Notice>
          <p className="text-lg font-semibold">{results.statement}</p>
        </Notice>
      )}

      <h2>What will be reported</h2>
      <p>
        When the pre-registered analyses have been run, this page will show the following, generated only from
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
      <p>
        Negative and null findings will be reported with the same prominence as positive ones.
      </p>
    </article>
  );
}
