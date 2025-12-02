"use client";

import { useDeferredValue, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { EmailSummary } from "@/lib/types";
import {
  Card,
  CardContent,
  CardDescription,
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { Loader2, RefreshCw, Eye, Mail, Calendar, User, Link as LinkIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";

// Email categories matching backend schema
const EMAIL_CATEGORIES = [
  { value: "contract", label: "Contract" },
  { value: "invoice", label: "Invoice" },
  { value: "proposal", label: "Proposal" },
  { value: "design_document", label: "Design Document" },
  { value: "correspondence", label: "Correspondence" },
  { value: "internal", label: "Internal" },
  { value: "financial", label: "Financial" },
  { value: "rfi", label: "RFI/Submittal" },
  { value: "presentation", label: "Presentation" },
];

// Fallback categories for filters (includes more common ones)
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
    design_document: [
      { value: "concept", label: "Concept" },
      { value: "schematic", label: "Schematic" },
      { value: "detail", label: "Detail Design" },
      { value: "revision", label: "Revision" },
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
  const [previewEmail, setPreviewEmail] = useState<EmailSummary | null>(null);
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

  // Query for email detail when preview is opened
  const emailDetailQuery = useQuery({
    queryKey: ["email-detail", previewEmail?.email_id],
    queryFn: () => api.getEmailDetail(previewEmail!.email_id),
    enabled: !!previewEmail?.email_id,
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
      setPreviewEmail(null); // Close preview modal after save
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
    const email = findEmail(emailId) || previewEmail;
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

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return "Unknown date";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: date.getFullYear() !== new Date().getFullYear() ? "numeric" : undefined,
      });
    } catch {
      return "Invalid date";
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Email Category Corrections
          </h1>
          <p className="text-muted-foreground mt-2">
            Fix AI mistakes and improve categorization accuracy
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-sm text-muted-foreground">
            {emails.length} emails pending review
          </div>
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

      {/* Category Overview Cards */}
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
                "cursor-pointer transition hover:border-primary hover:shadow-sm",
                categoryFilter === item.value && "border-primary shadow-sm bg-primary/5"
              )}
              onClick={() =>
                setCategoryFilter((prev) =>
                  prev === item.value ? undefined : item.value
                )
              }
            >
              <CardContent className="py-4">
                <p className="text-xs uppercase text-muted-foreground mb-1">
                  {item.value === categoryFilter ? "Filtering by" : "Category"}
                </p>
                <div className="flex items-center justify-between">
                  <p className="text-lg font-semibold capitalize">
                    {item.label.replace(/_/g, " ")}
                  </p>
                  <Badge variant="secondary">{item.count ?? 0}</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
      </div>

      {/* Email List */}
      <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle className="text-xl font-semibold">
                Uncategorized or Uncertain Emails
              </CardTitle>
              <CardDescription className="mt-1.5">
                Review and correct email categories to train the AI
              </CardDescription>
            </div>
            {categoryFilter && (
              <Badge variant="outline" className="capitalize">
                Filtering: {categoryFilter.replace(/_/g, " ")}
              </Badge>
            )}
          </div>
          <div className="flex flex-wrap gap-3">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search subject or sender..."
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
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : emails.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">
              <Mail className="h-12 w-12 mx-auto mb-4 opacity-20" />
              <p className="text-lg font-medium">No emails match this filter</p>
              <p className="text-sm mt-1">Try adjusting your search or filter criteria</p>
            </div>
          ) : (
            <ScrollArea className="max-h-[640px]">
              <Table className="table-fixed">
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[35%]">Email</TableHead>
                    <TableHead className="w-[15%]">Current</TableHead>
                    <TableHead className="w-[20%]">Correct Category</TableHead>
                    <TableHead className="w-[15%]">Subcategory</TableHead>
                    <TableHead className="w-[15%] text-right">Actions</TableHead>
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
                    const linkedProject = email.project_code;
                    const isActive = email.is_active_project === 1;

                    return (
                      <TableRow key={email.email_id} className="group">
                        <TableCell className="align-top">
                          <div className="space-y-2">
                            <div className="flex items-start gap-2">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 flex-shrink-0 opacity-0 group-hover:opacity-100 transition"
                                onClick={() => setPreviewEmail(email)}
                                title="Preview email"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <div className="flex-1 min-w-0">
                                <p
                                  className="font-medium text-sm truncate cursor-pointer hover:text-primary"
                                  onClick={() => setPreviewEmail(email)}
                                  title={email.subject || "No subject"}
                                >
                                  {email.subject || "(No subject)"}
                                </p>
                                <p className="text-xs text-muted-foreground truncate mt-0.5">
                                  <User className="h-3 w-3 inline mr-1" />
                                  {email.sender_email}
                                </p>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                  <Calendar className="h-3 w-3 inline mr-1" />
                                  {formatDate(email.date)}
                                </p>
                              </div>
                            </div>
                            {email.snippet && (
                              <p className="text-xs text-muted-foreground line-clamp-2 pl-10">
                                {email.snippet}
                              </p>
                            )}
                            {linkedProject && (
                              <div className="pl-10">
                                <Link
                                  href={isActive ? `/projects/${linkedProject}` : `/tracker?project=${linkedProject}`}
                                  className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                                >
                                  <LinkIcon className="h-3 w-3" />
                                  {linkedProject} {isActive ? "(Active)" : "(Proposal)"}
                                </Link>
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="align-top">
                          <Badge variant="secondary" className="capitalize">
                            {email.category ?? "uncategorized"}
                          </Badge>
                          {email.subcategory && (
                            <p className="text-xs text-muted-foreground mt-1">
                              {email.subcategory}
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
                              {EMAIL_CATEGORIES.map((item) => {
                                const disabled =
                                  item.value === "rfi" && !isActive;
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
                              <SelectValue placeholder="Subcategory" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">None</SelectItem>
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
                            <p className="text-[10px] text-muted-foreground mt-1">
                              N/A
                            </p>
                          )}
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
            Page {page} of {totalPages} • {emailsQuery.data?.pagination.total ?? 0} total emails
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

      {/* Email Preview Modal */}
      <Dialog open={!!previewEmail} onOpenChange={() => setPreviewEmail(null)}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="text-xl pr-8">
              {previewEmail?.subject || "(No subject)"}
            </DialogTitle>
            <DialogDescription>
              Review full email content and correct the category
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="flex-1 pr-4">
            {previewEmail && (
              <div className="space-y-6">
                {/* Email Metadata */}
                <div className="grid grid-cols-2 gap-4 p-4 bg-muted/50 rounded-lg">
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">From</Label>
                    <p className="text-sm font-medium">{previewEmail.sender_email}</p>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">Date</Label>
                    <p className="text-sm">{formatDate(previewEmail.date)}</p>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">Current Category</Label>
                    <Badge variant="secondary" className="capitalize">
                      {previewEmail.category ?? "uncategorized"}
                    </Badge>
                  </div>
                  {previewEmail.project_code && (
                    <div className="space-y-1">
                      <Label className="text-xs text-muted-foreground">Linked Project</Label>
                      <Link
                        href={
                          previewEmail.is_active_project === 1
                            ? `/projects/${previewEmail.project_code}`
                            : `/tracker?project=${previewEmail.project_code}`
                        }
                        className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                      >
                        <LinkIcon className="h-3 w-3" />
                        {previewEmail.project_code}
                        {previewEmail.is_active_project === 1 ? " (Active)" : " (Proposal)"}
                      </Link>
                    </div>
                  )}
                </div>

                {/* Email Body */}
                <div>
                  <Label className="text-sm font-semibold mb-2 block">Email Content</Label>
                  <div className="border rounded-lg p-4 bg-background">
                    {emailDetailQuery.isLoading ? (
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-4/5" />
                        <Skeleton className="h-4 w-full" />
                      </div>
                    ) : emailDetailQuery.data?.body_full ? (
                      <div className="prose prose-sm max-w-none">
                        <pre className="whitespace-pre-wrap font-sans text-sm">
                          {emailDetailQuery.data.body_full}
                        </pre>
                      </div>
                    ) : (
                      <p className="text-muted-foreground text-sm">
                        {previewEmail.snippet || "No content available"}
                      </p>
                    )}
                  </div>
                </div>

                {/* Category Correction UI */}
                <div className="border-t pt-6 space-y-4">
                  <h3 className="font-semibold text-lg">Correct This Email</h3>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="preview-category">Correct Category *</Label>
                      <Select
                        value={
                          getEffectiveCategory(
                            previewEmail,
                            drafts[previewEmail.email_id]
                          ) || "uncategorized"
                        }
                        onValueChange={(newValue) =>
                          handleCategorySelect(
                            previewEmail,
                            newValue === "uncategorized" ? "" : newValue
                          )
                        }
                      >
                        <SelectTrigger id="preview-category">
                          <SelectValue placeholder="Pick category" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="uncategorized">Select...</SelectItem>
                          {EMAIL_CATEGORIES.map((item) => {
                            const disabled =
                              item.value === "rfi" &&
                              previewEmail.is_active_project !== 1;
                            return (
                              <SelectItem
                                key={item.value}
                                value={item.value}
                                disabled={disabled}
                              >
                                {item.label}
                                {disabled ? " (active only)" : ""}
                              </SelectItem>
                            );
                          })}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="preview-subcategory">Subcategory</Label>
                      <Select
                        value={
                          SUBCATEGORY_OPTIONS[
                            getEffectiveCategory(
                              previewEmail,
                              drafts[previewEmail.email_id]
                            )
                          ]?.length
                            ? getEffectiveSubcategory(
                                previewEmail,
                                drafts[previewEmail.email_id]
                              ) || "none"
                            : "none"
                        }
                        disabled={
                          !SUBCATEGORY_OPTIONS[
                            getEffectiveCategory(
                              previewEmail,
                              drafts[previewEmail.email_id]
                            )
                          ]?.length
                        }
                        onValueChange={(newValue) =>
                          handleDraftChange(
                            previewEmail.email_id,
                            "subcategory",
                            newValue === "none" ? undefined : newValue
                          )
                        }
                      >
                        <SelectTrigger id="preview-subcategory">
                          <SelectValue placeholder="Subcategory" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">None</SelectItem>
                          {(
                            SUBCATEGORY_OPTIONS[
                              getEffectiveCategory(
                                previewEmail,
                                drafts[previewEmail.email_id]
                              )
                            ] ?? []
                          ).map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="preview-notes">Notes</Label>
                    <Textarea
                      id="preview-notes"
                      placeholder="Add notes about this correction (optional)..."
                      className="min-h-[120px] resize-none"
                      rows={5}
                      value={drafts[previewEmail.email_id]?.feedback ?? ""}
                      onChange={(event) =>
                        handleDraftChange(
                          previewEmail.email_id,
                          "feedback",
                          event.target.value
                        )
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Explain why this category is correct to help train the AI
                    </p>
                  </div>

                  <div className="flex justify-end gap-2 pt-4">
                    <Button
                      variant="outline"
                      onClick={() => setPreviewEmail(null)}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={() => handleSubmit(previewEmail.email_id)}
                      disabled={mutation.isPending}
                    >
                      {mutation.isPending && (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      )}
                      Save Correction
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Syncing Indicator */}
      {showSyncing && (
        <div className="fixed inset-x-0 bottom-4 flex justify-center pointer-events-none">
          <div className="rounded-full bg-background px-4 py-2 text-sm shadow-lg border">
            <Loader2 className="inline h-4 w-4 mr-2 animate-spin" />
            Syncing latest data…
          </div>
        </div>
      )}
    </div>
  );
}
