import DashboardLayout from "@/components/DashboardLayout";
import RagSearchTester from "@/components/RagSearchTester";

export default function RagTestPage() {
  return (
    <DashboardLayout
      title="Knowledge Search"
      subtitle="Preview which business documents the assistant will use for an answer."
    >
      <RagSearchTester />
    </DashboardLayout>
  );
}
