import { Metadata } from "next";
import QueryInterface from "@/components/query-interface";

export const metadata: Metadata = {
  title: "Query Intelligence | Bensley Operations",
  description: "Ask natural language questions about your projects, proposals, invoices, and emails.",
};

export default function QueryPage() {
  return (
    <div className="w-full max-w-full py-6 overflow-x-hidden">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Query Intelligence</h1>
        <p className="text-gray-600 mt-2">
          Ask questions about your projects, proposals, invoices, and emails in natural language.
        </p>
      </div>

      <QueryInterface />
    </div>
  );
}
