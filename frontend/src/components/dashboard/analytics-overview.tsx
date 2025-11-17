import { AnalyticsDashboard } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Activity, Mail, FileText } from "lucide-react";

type Props = {
  data?: AnalyticsDashboard;
  isLoading?: boolean;
};

const cards = [
  {
    key: "proposals",
    title: "Proposals",
    icon: Activity,
    getContent: (data: AnalyticsDashboard["proposals"]) => [
      { label: "Total", value: data.total_proposals },
      { label: "Active", value: data.active_projects },
      { label: "At Risk", value: data.at_risk },
    ],
  },
  {
    key: "emails",
    title: "Emails",
    icon: Mail,
    getContent: (data: AnalyticsDashboard["emails"]) => [
      { label: "Total", value: data.total_emails },
      { label: "Processed", value: data.processed },
      { label: "Linked", value: data.linked_to_proposals },
    ],
  },
  {
    key: "documents",
    title: "Documents",
    icon: FileText,
    getContent: (data: AnalyticsDashboard["documents"]) => [
      { label: "Total", value: data.total_documents },
      { label: "Linked", value: data.linked_to_proposals },
      { label: "Common Type", value: data.most_common_type },
    ],
  },
];

export default function AnalyticsOverview({ data, isLoading }: Props) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {cards.map((card) => {
        const InfoIcon = card.icon;
        const content =
          data && (card.key as keyof AnalyticsDashboard) in data
            ? card.getContent(
                data[card.key as keyof AnalyticsDashboard] as never
              )
            : [];

        return (
          <Card key={card.key} className="h-full">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {card.title}
              </CardTitle>
              <InfoIcon className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-6 w-24" />
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-28" />
                </div>
              ) : (
                <div className="space-y-2">
                  {content.map((item) => (
                    <div
                      key={item.label}
                      className="flex items-center justify-between"
                    >
                      <span className="text-sm text-muted-foreground">
                        {item.label}
                      </span>
                      {typeof item.value === "string" ? (
                        <Badge variant="secondary">{item.value}</Badge>
                      ) : (
                        <span className="text-lg font-semibold">
                          {item.value ?? "—"}
                        </span>
                      )}
                    </div>
                  ))}
                  {data?.timestamp && (
                    <p className="text-xs text-muted-foreground">
                      Updated {new Date(data.timestamp).toLocaleString()}
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
