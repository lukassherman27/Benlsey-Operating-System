import { TimelineEmail } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MailWarning, Mail } from "lucide-react";

type Props = {
  emails?: TimelineEmail[];
  isLoading?: boolean;
};

function formatDate(date?: string) {
  if (!date) return "Unknown date";
  return new Date(date).toLocaleString();
}

export default function EmailPanel({ emails, isLoading }: Props) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Mail className="h-5 w-5 text-primary" />
          Email Intelligence
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Categorized emails linked to this proposal
        </p>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="space-y-2 p-6">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : emails && emails.length > 0 ? (
          <ScrollArea className="h-[320px]">
            <div className="divide-y">
              {emails.map((email) => (
                <div key={email.email_id} className="p-4">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium">{email.subject}</p>
                    <Badge variant="outline" className="capitalize">
                      {email.category ?? "uncategorized"}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {email.sender_email} • {formatDate(email.date)}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    {email.importance_score != null && (
                      <span>
                        Importance: {Math.round(email.importance_score * 100)}%
                      </span>
                    )}
                    {email.follow_up_date && (
                      <span>
                        Follow-up:{" "}
                        {new Date(email.follow_up_date).toLocaleDateString()}
                      </span>
                    )}
                    {email.action_required ? (
                      <Badge
                        variant="destructive"
                        className="flex items-center gap-1 text-[10px]"
                      >
                        <MailWarning className="h-3 w-3" />
                        Action required
                      </Badge>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        ) : (
          <div className="p-6 text-center text-sm text-muted-foreground">
            No emails linked to this proposal yet.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
