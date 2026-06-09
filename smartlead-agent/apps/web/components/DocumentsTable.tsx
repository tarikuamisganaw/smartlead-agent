import type { ReactNode } from "react";
import type { DocumentInfo } from "@/lib/types";
import { formatDateTime, shortId } from "@/lib/utils";

export default function DocumentsTable({ documents }: { documents: DocumentInfo[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-line bg-white shadow-sm">
      <table className="min-w-[760px] w-full border-collapse text-left text-sm">
        <thead className="bg-panel text-xs uppercase text-ink/50">
          <tr>
            <Th>Title</Th>
            <Th>Source</Th>
            <Th>Chunks</Th>
            <Th>Created</Th>
            <Th>Document ID</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {documents.map((document) => (
            <tr key={document.id}>
              <Td><span className="font-semibold text-ink">{document.title}</span></Td>
              <Td><span className="break-all">{document.source}</span></Td>
              <Td>{document.chunk_count}</Td>
              <Td>{formatDateTime(document.created_at)}</Td>
              <Td>{shortId(document.id)}</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: ReactNode }) {
  return <th className="px-4 py-3 font-semibold">{children}</th>;
}

function Td({ children }: { children: ReactNode }) {
  return <td className="px-4 py-3 text-ink/75">{children}</td>;
}
