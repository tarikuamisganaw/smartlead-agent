import DashboardLayout from "@/components/DashboardLayout";
import RagSearchTester from "@/components/RagSearchTester";

export default function RagTestPage() {
  return (
    <DashboardLayout
      title="RAG Test"
      subtitle="Search the ingested demo business chunks using the same local TF-IDF retrieval service as the agent workflow."
    >
      <RagSearchTester />
    </DashboardLayout>
  );
}
