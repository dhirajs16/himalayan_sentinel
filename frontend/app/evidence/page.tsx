import Link from "next/link";
import EvidenceExplorer from "@/components/evidence-explorer";

export default async function EvidencePage({ searchParams }: { searchParams: Promise<{ district?: string }> }) {
  const parameters = await searchParams;
  const district = typeof parameters.district === "string" ? parameters.district.slice(0, 80) : undefined;
  return <main className="shell">
    <nav aria-label="Evidence navigation" className="header-actions"><Link href="/">Public dashboard</Link><Link href="/operations">Staff workspace</Link></nav>
    <EvidenceExplorer initialDistrict={district} />
  </main>;
}
