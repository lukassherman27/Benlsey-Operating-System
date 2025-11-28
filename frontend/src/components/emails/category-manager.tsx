"use client";

import { useDeferredValue, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { EmailSummary } from "@/lib/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { Loader2, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

const BASE_CATEGORIES = [
  "general",
  "proposal",
  "project_update",
  "design",
  "contract",
  "invoice",
  "rfi",
  "schedule",
  "meeting",
  "project_admin",
  "vendor",
  "internal",
];

const SUBCATEGORY_OPTIONS: Record<string, { value: string; label: string }[]> =
  {
    contract: [
      { value: "proposal", label: "Proposal" },
      { value: "mou", label: "MOU" },
      { value: "nda", label: "NDA" },
      { value: "service", label: "Service Agreement" },
      { value: "amendment", label: "Amendment" },
    ],
    invoice: [
      { value: "initial", label: "Initial" },
      { value: "milestone", label: "Milestone" },
      { value: "final", label: "Final" },
      { value: "expense", label: "Expense" },
    ],
    design: [
      { value: "concept", label: "Concept" },
      { value: "schematic", label: "Schematic" },
      { value: "detail", label: "Detail Design" },
      { value: "revision", label: "Revision" },
      { value: "approval", label: "Approval" },
    ],
    meeting: [
      { value: "kickoff", label: "Kickoff" },
      { value: "review", label: "Review" },
      { value: "client", label: "Client" },
      { value: "internal", label: "Internal" },
    ],
    project_update: [
      { value: "status", label: "Status" },
      { value: "milestone", label: "Milestone" },
      { value: "issue", label: "Issue/Risk" },
    ],
  };

type Draft = {
  category?: string;
  subcategory?: string;
  feedback?: string;
};

type DraftMap = Record<number, Draft>;

export default function EmailCategoryManager() {
  const [categoryFilter, setCategoryFilter] = useState<string>();
  const [searchInput, setSearchInput] = useState("");
  const deferredSearch = useDeferredValue(searchInput.trim());
  const searchValue = deferredSearch.length ? deferredSearch : undefined;
  const [page, setPage] = useState(1);
  const [drafts, setDrafts] = useState<DraftMap>({});
  const perPage = 10;

  const categoriesQuery = useQuery({
    queryKey: ["email-categories"],
    queryFn: api.getEmailCategories,
    staleTime: 1000 * 60 * 5,
  });

  const categoryListQuery = useQuery({
    queryKey: ["email-categories-list"],
    queryFn: api.getEmailCategoryList,
    staleTime: 1000 * 60 * 10,
  });

  const emailsQuery = useQuery({
    queryKey: ["emails", { category: categoryFilter, page, perPage, search: searchValue }],
    queryFn: () =>
      api.getEmails({
        category: categoryFilter,
        page,
        per_page: perPage,
        q: searchValue,
        sort_by: "date",
        sort_order: "DESC",
      }),
  });

  const mutation = useMutation({
    mutationFn: ({
      emailId,
      category,
      subcategory,
      feedback,
    }: {
      emailId: number;
      category: string;
      subcategory?: string | null;
      feedback?: string;
    }) =>
      api.updateEmailCategory(emailId, { category, subcategory, feedback }),
    onSuccess: (_, variables) => {
      toast.success("Category updated", {
        description: "Thanks! Training data saved.",
      });
      setDrafts((prev) => {
        const next = { ...prev };
        delete next[variables.emailId];
        return next;
      });
      emailsQuery.refetch();
      categoriesQuery.refetch();
      categoryListQuery.refetch();
    },
    onError: (error: Error) => {
      toast.error("Unable to save correction", {
        description: error.message,
      });
    },
  });

  const categoryCounts = useMemo(
    () => categoriesQuery.data ?? {},
    [categoriesQuery.data]
  );
  const categoryList =
    categoryListQuery.data?.categories ??
    Object.keys(categoryCounts).map((key) => ({
      value: key,
      label: key,
      count: categoryCounts[key] ?? 0,
    }));
  const mappedCategories = categoryList.length
    ? categoryList
    : BASE_CATEGORIES.map((value) => ({
        value,
        label: value,
      }));

  const emails = useMemo(
    () => emailsQuery.data?.data ?? [],
    [emailsQuery.data]
  );

  const totalPages = emailsQuery.data?.pagination.total_pages ?? 1;

  const findEmail = (emailId: number) =>
    emails.find((email) => email.email_id === emailId);

  const getEffectiveCategory = (email: EmailSummary, draft?: Draft) =>
    draft?.category ?? email.category ?? "";

  const getEffectiveSubcategory = (email: EmailSummary, draft?: Draft) =>
    draft?.subcategory ?? email.subcategory ?? "";

  const handleCategorySelect = (email: EmailSummary, nextValue: string) => {
    const normalized = nextValue || undefined;
    const requiresActive = normalized === "rfi";
    if (requiresActive && email.is_active_project !== 1) {
      toast.error("RFIs only apply to active projects.");
      return;
    }

    handleDraftChange(email.email_id, "category", normalized);

    const options = SUBCATEGORY_OPTIONS[normalized ?? ""] ?? [];
    if (!options.length) {
      handleDraftChange(email.email_id, "subcategory", undefined);
      return;
    }

    const currentSubcategory = getEffectiveSubcategory(
      email,
      drafts[email.email_id]
    );
    if (!options.some((opt) => opt.value === currentSubcategory)) {
      handleDraftChange(email.email_id, "subcategory", undefined);
    }
  };

  const updateDraft = (emailId: number, partial: Partial<Draft>) => {
    setDrafts((prev) => {
      const current = prev[emailId] ?? {};
      const next: Draft = {
        ...current,
        ...partial,
      };
      const shouldRemove =
        !next.category && !next.subcategory && !next.feedback;
      if (shouldRemove) {
        const copy = { ...prev };
        delete copy[emailId];
        return copy;
      }
      return { ...prev, [emailId]: next };
    });
  };

  const handleDraftChange = (
    emailId: number,
    field: keyof Draft,
    value?: string | null
  ) => {
    updateDraft(emailId, { [field]: value ?? undefined } as Partial<Draft>);
  };

  const handleSubmit = (emailId: number) => {
    const email = findEmail(emailId);
    if (!email) return;
    const draft = drafts[emailId];
    const finalCategory = getEffectiveCategory(email, draft);

    if (!finalCategory) {
      toast.error("Choose a category before saving.");
      return;
    }

    const subcategoryOptions = SUBCATEGORY_OPTIONS[finalCategory] ?? [];
    const finalSubcategory = subcategoryOptions.length
      ? getEffectiveSubcategory(email, draft)
      : undefined;

    mutation.mutate({
      emailId,
      category: finalCategory,
      subcategory:
        finalSubcategory && finalSubcategory.length > 0
          ? finalSubcategory
          : null,
      feedback: draft?.feedback,
    });
  };

  const handleReset = (emailId: number) => {
    setDrafts((prev) => {
      const next = { ...prev };
      delete next[emailId];
      return next;
    });
  };

  const isInitialLoading =
    categoriesQuery.isLoading ||
    categoryListQuery.isLoading ||
    emailsQuery.isLoading;
  const showSyncing =
    (emailsQuery.isFetching ||
      categoriesQuery.isFetching ||
      categoryListQuery.isFetching) &&
    !isInitialLoading;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Email Category Corrections
          </h1>
          <p className="text-sm text-muted-foreground">
            Fix AI mistakes and instantly add examples to the training set.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              categoriesQuery.refetch();
              emailsQuery.refetch();
            }}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </header>

      {(categoriesQuery.error || emailsQuery.error || categoryListQuery.error) && (
        <div className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
          {categoriesQuery.error instanceof Error && (
            <p>
              Failed to load category counts: {categoriesQuery.error.message}
            </p>
          )}
          {categoryListQuery.error instanceof Error && (
            <p>Category list unavailable: {categoryListQuery.error.message}</p>
          )}
          {emailsQuery.error instanceof Error && (
            <p>Unable to load emails: {emailsQuery.error.message}</p>
          )}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {(categoryList.length
          ? categoryList
          : BASE_CATEGORIES.map((cat) => ({
              value: cat,
              label: cat,
              count: 0,
            }))
        )
          .slice(0, 8)
          .map((item) => (
            <Card
              key={item.value}
              className={cn(
                "cursor-pointer transition hover:border-primary",
                categoryFilter === item.value && "border-primary shadow-sm"
              )}
              onClick={() =>
                setCategoryFilter((prev) =>
                  prev === item.value ? undefined : item.value
                )
              }
            >
              <CardContent className="py-4">
                <p className="text-xs uppercase text-muted-foreground">
                  {item.value === categoryFilter ? "Filtering by" : "Category"}
                </p>
                <div className="flex items-center justify-between">
                  <p className="text-lg font-semibold capitalize">
                    {item.label}
                  </p>
                  <Badge variant="secondary">{item.count}</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
      </div>

      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <CardTitle className="text-lg font-semibold">
              Review Emails
            </CardTitle>
            {categoryFilter && (
              <Badge variant="outline" className="capitalize">
                Filtering: {categoryFilter}
              </Badge>
            )}
          </div>
          <div className="flex flex-wrap gap-3">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search subject or sender"
                value={searchInput}
                onChange={(event) => {
                  setPage(1);
                  setSearchInput(event.target.value);
                }}
              />
            </div>
            <div className="w-full min-[460px]:w-48">
              <Select
                value={categoryFilter ?? "all"}
                onValueChange={(value) => {
                  setPage(1);
                  setCategoryFilter(value === "all" ? undefined : value);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Filter category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All categories</SelectItem>
                  {mappedCategories.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
        {emailsQuery.isLoading ? (
            <div className="space-y-2 p-6">
              <Skeleton className="h-6 w-full" />
              <Skeleton className="h-6 w-full" />
              <Skeleton className="h-6 w-full" />
            </div>
          ) : emails.length === 0 ? (
            <div className="p-8 text-center text-sm text-muted-foreground">
              No emails match this filter just yet.
            </div>
          ) : (
            <ScrollArea className="max-h-[640px]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>Current</TableHead>
                    <TableHead>Correct Category</TableHead>
                    <TableHead>Subcategory</TableHead>
                    <TableHead>Notes</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {emails.map((email) => {
                    const draft = drafts[email.email_id];
                    const categoryValue = getEffectiveCategory(email, draft);
                    const subcategoryValue = getEffectiveSubcategory(
                      email,
                      draft
                    );
                    const subcategoryOptions =
                      SUBCATEGORY_OPTIONS[categoryValue] ?? [];
                    const linkedProject = email.project_code
                      ? `${email.project_code} ${
                          email.is_active_project === 1 ? "(Active)" : "(Proposal)"
                        }`
                      : "Unlinked";
                    return (
                      <TableRow key={email.email_id}>
                        <TableCell className="align-top">
                          <p className="font-medium">{email.subject}</p>
                          <p className="text-xs text-muted-foreground">
                            {email.sender_email}
                          </p>
                          <p className="mt-2 text-xs text-muted-foreground">
                            {email.snippet ?? "No preview available"}
                          </p>
                          <p className="mt-2 text-xs text-muted-foreground">
                            {linkedProject}
                          </p>
                        </TableCell>
                        <TableCell className="align-top">
                          <Badge variant="secondary" className="capitalize">
                            {email.category ?? "uncategorized"}
                          </Badge>
                          {email.subcategory && (
                            <p className="text-xs text-muted-foreground">
                              Subcategory: {email.subcategory}
                            </p>
                          )}
                        </TableCell>
                        <TableCell className="align-top">
                          <Select
                            value={categoryValue || "uncategorized"}
                            onValueChange={(newValue) =>
                              handleCategorySelect(
                                email,
                                newValue === "uncategorized" ? "" : newValue
                              )
                            }
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Pick category" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="uncategorized">
                                Select...
                              </SelectItem>
                              {mappedCategories.map((item) => {
                                const disabled =
                                  item.value === "rfi" &&
                                  email.is_active_project !== 1;
                                return (
                                  <SelectItem
                                    key={item.value}
                                    value={item.value}
                                    disabled={disabled}
                                    title={
                                      disabled
                                        ? "RFIs require an active project."
                                        : undefined
                                    }
                                  >
                                    {item.label}
                                    {disabled ? " (active only)" : ""}
                                  </SelectItem>
                                );
                              })}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell className="align-top">
                          <Select
                            value={
                              subcategoryOptions.length
                                ? subcategoryValue || "none"
                                : "none"
                            }
                            disabled={!subcategoryOptions.length}
                            onValueChange={(newValue) =>
                              handleDraftChange(
                                email.email_id,
                                "subcategory",
                                newValue === "none" ? undefined : newValue
                              )
                            }
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select subcategory" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">No subcategory</SelectItem>
                              {subcategoryOptions.map((option) => (
                                <SelectItem
                                  key={option.value}
                                  value={option.value}
                                >
                                  {option.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          {!subcategoryOptions.length && (
                            <p className="text-xs text-muted-foreground">
                              Not required for this category.
                            </p>
                          )}
                        </TableCell>
                        <TableCell className="align-top">
                          <Textarea
                            rows={3}
                            placeholder="Optional note (why this category?)"
                            value={draft?.feedback ?? ""}
                            onChange={(event) =>
                              handleDraftChange(
                                email.email_id,
                                "feedback",
                                event.target.value
                              )
                            }
                          />
                        </TableCell>
                        <TableCell className="align-top text-right">
                          <div className="flex flex-col items-end gap-2">
                            <Button
                              size="sm"
                              onClick={() => handleSubmit(email.email_id)}
                              disabled={
                                mutation.isPending &&
                                mutation.variables?.emailId === email.email_id
                              }
                            >
                              {mutation.isPending &&
                              mutation.variables?.emailId === email.email_id ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              ) : null}
                              Save
                            </Button>
                            {draft && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleReset(email.email_id)}
                              >
                                Reset
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </ScrollArea>
          )}
        </CardContent>
        <div className="flex items-center justify-between border-t px-6 py-4 text-sm">
          <p className="text-muted-foreground">
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() =>
                setPage((prev) => Math.min(totalPages, prev + 1))
              }
            >
              Next
            </Button>
          </div>
        </div>
      </Card>

      {showSyncing && (
        <div className="fixed inset-x-0 bottom-4 flex justify-center">
          <div className="rounded-full bg-background px-4 py-2 text-sm shadow-lg">
            Syncing latest data…
          </div>
        </div>
      )}
    </div>
  );
}
