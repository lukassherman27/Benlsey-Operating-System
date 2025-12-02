import { ProposalTimelineResponse } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { CalendarClock, Mail, FileText, Activity } from "lucide-react";

type Props = {
  data?: ProposalTimelineResponse;
  isLoading?: boolean;
};

const iconMap: Record<string, React.ReactNode> = {
  email: <Mail className="h-4 w-4 text-primary" />,
  document: <FileText className="h-4 w-4 text-primary" />,
};

function formatDate(date: string) {
  const d = new Date(date);
  return d.toLocaleString();
}

export default function TimelinePanel({ data, isLoading }: Props) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarClock className="h-5 w-5 text-primary" />
          Proposal Timeline
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Combined stream of emails, documents, and milestones
        </p>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="space-y-2 p-6">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : data && data.timeline.length > 0 ? (
          <ScrollArea className="h-[320px]">
            <div className="space-y-0">
              {data.timeline.map((event, index) => (
                <div
                  key={`${event.type}-${event.date}-${index}`}
                  className="flex items-start gap-3 border-b p-4 last:border-0"
                >
                  <div className="mt-1">
                    {iconMap[event.type] ?? (
                      <Activity className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-semibold capitalize">
                      {event.type.replaceAll("_", " ")}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(String(event.date))}
                    </p>
                    {"subject" in event && typeof event.subject === "string" && event.subject ? (
                      <p className="text-sm">{event.subject}</p>
                    ) : null}
                    {"file_name" in event && typeof event.file_name === "string" && event.file_name ? (
                      <p className="text-sm">{event.file_name}</p>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        ) : (
          <div className="p-6 text-center text-sm text-muted-foreground">
            Timeline will populate as we ingest more events.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
