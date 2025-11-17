import { QueryResponse, QuerySuggestionsResponse } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Sparkles, Lightbulb } from "lucide-react";
import { useState } from "react";

type Props = {
  suggestions?: QuerySuggestionsResponse;
  onSubmit: (question: string) => Promise<QueryResponse>;
  variant?: "card" | "panel";
  title?: string;
  description?: string;
};

export default function QueryPanel({
  suggestions,
  onSubmit,
  variant = "card",
  title = "Query Brain",
  description = "Ask natural language questions against the Bensley intelligence DB",
}: Props) {
  const [question, setQuestion] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!question.trim()) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await onSubmit(question.trim());
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const body = (
    <div className="space-y-4">
      <Textarea
        placeholder="e.g. Why hasn't BK-069 been signed yet?"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        rows={4}
      />
      <div className="flex justify-end">
        <Button onClick={handleSubmit} disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Run Query
        </Button>
      </div>

      {result && (
        <div className="rounded-lg border bg-muted/20 p-4">
          <p className="text-sm text-muted-foreground">Answer</p>
          {result.success ? (
            <>
              <p className="mt-2 text-sm">
                {result.results.length > 0
                  ? JSON.stringify(result.results[0], null, 2)
                  : "No results returned."}
              </p>
              {result.sql && (
                <p className="mt-3 text-xs font-mono text-muted-foreground">
                  SQL: {result.sql}
                </p>
              )}
            </>
          ) : (
            <p className="text-sm text-destructive">
              {result.error ?? "Query failed"}
            </p>
          )}
        </div>
      )}

      {error && (
        <p className="text-sm text-destructive">
          Something went wrong: {error}
        </p>
      )}

      {suggestions && (
        <div className="space-y-3 rounded-lg border bg-card p-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Lightbulb className="h-4 w-4 text-yellow-500" />
            Quick Suggestions
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestions.suggestions.slice(0, 6).map((suggestion) => (
              <Badge
                key={suggestion}
                variant="outline"
                className="cursor-pointer"
                onClick={() => setQuestion(suggestion)}
              >
                {suggestion}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {suggestions?.types && (
        <ScrollArea className="h-32 rounded-lg border bg-card p-4">
          <div className="space-y-3 text-xs">
            {suggestions.types.map((type) => (
              <div key={type.type}>
                <p className="font-semibold capitalize">{type.type}</p>
                <p className="text-muted-foreground">{type.description}</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {type.examples.map((example) => (
                    <Badge
                      key={example}
                      variant="secondary"
                      className="cursor-pointer"
                      onClick={() => setQuestion(example)}
                    >
                      {example}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );

  if (variant === "panel") {
    return (
      <div className="flex h-full flex-col space-y-4">
        <div>
          <div className="flex items-center gap-2 text-lg font-semibold">
            <Sparkles className="h-5 w-5 text-primary" />
            {title}
          </div>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
        {body}
      </div>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          {title}
        </CardTitle>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardHeader>
      <CardContent>{body}</CardContent>
    </Card>
  );
}
