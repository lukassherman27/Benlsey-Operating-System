import { TimelineDocument } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { FileText } from "lucide-react";

type Props = {
  documents?: TimelineDocument[];
  isLoading?: boolean;
};

export default function DocumentPanel({ documents, isLoading }: Props) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          Documents
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Latest files linked to this proposal
        </p>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="space-y-2 p-6">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : documents && documents.length > 0 ? (
          <ScrollArea className="h-[320px]">
            <div className="divide-y">
              {documents.map((doc) => (
                <div key={doc.document_id} className="flex items-center justify-between gap-3 p-4">
                  <div>
                    <p className="font-medium">{doc.file_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {doc.modified_date
                        ? new Date(doc.modified_date).toLocaleDateString()
                        : "Unknown date"}
                    </p>
                  </div>
                  <Badge variant="secondary" className="capitalize">
                    {doc.document_type ?? "document"}
                  </Badge>
                </div>
              ))}
            </div>
          </ScrollArea>
        ) : (
          <div className="p-6 text-center text-sm text-muted-foreground">
            No documents linked yet.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
