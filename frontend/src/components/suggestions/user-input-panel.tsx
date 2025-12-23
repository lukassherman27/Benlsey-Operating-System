"use client";

import { useState } from "react";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { X } from "lucide-react";
import { UserContext, SuggestionTag } from "@/lib/types";

const CONTACT_ROLES = [
  { value: 'client', label: 'Client' },
  { value: 'client_contact', label: 'Client Contact' },
  { value: 'contractor', label: 'Contractor' },
  { value: 'consultant', label: 'Consultant' },
  { value: 'vendor', label: 'Vendor' },
  { value: 'architect', label: 'Architect' },
  { value: 'engineer', label: 'Engineer' },
  { value: 'project_manager', label: 'Project Manager' },
  { value: 'other', label: 'Other' },
];

const PRIORITIES = [
  { value: 'high', label: 'High', color: 'bg-red-100 text-red-700 border-red-200' },
  { value: 'medium', label: 'Medium', color: 'bg-amber-100 text-amber-700 border-amber-200' },
  { value: 'low', label: 'Low', color: 'bg-slate-100 text-slate-600 border-slate-200' },
];

interface UserInputPanelProps {
  userContext: UserContext;
  onChange: (context: UserContext) => void;
  availableTags?: SuggestionTag[];
  showPatternOptions?: boolean;
  createSenderPattern?: boolean;
  onSenderPatternChange?: (checked: boolean) => void;
  createDomainPattern?: boolean;
  onDomainPatternChange?: (checked: boolean) => void;
  senderEmail?: string;
  suggestionType?: string;
}

export function UserInputPanel({
  userContext,
  onChange,
  availableTags = [],
  showPatternOptions = false,
  createSenderPattern = false,
  onSenderPatternChange,
  createDomainPattern = false,
  onDomainPatternChange,
  senderEmail,
  suggestionType,
}: UserInputPanelProps) {
  const [tagInput, setTagInput] = useState("");
  const [showTagSuggestions, setShowTagSuggestions] = useState(false);

  // Internal Bensley domains - should never create patterns for internal staff emails
  const INTERNAL_DOMAINS = ['bensley.com', 'bensleydesign.com', 'bensley.co.th', 'bensley.id'];

  // Check if email is from an internal Bensley domain
  const isInternalEmail = (email: string | undefined): boolean => {
    if (!email || !email.includes('@')) return false;
    // Extract email from angle brackets if present (e.g., "Bill Bensley" <bill@bensley.com>)
    const match = email.match(/<([^>]+@[^>]+)>/);
    const cleanEmail = match ? match[1] : email;
    if (!cleanEmail.includes('@')) return false;
    const domain = cleanEmail.split('@')[1]?.toLowerCase();
    return domain ? INTERNAL_DOMAINS.includes(domain) : false;
  };

  // Extract domain from sender email, handling RFC 5322 format like "Name" <email@domain.com>
  // Returns undefined for internal Bensley domains (shouldn't create patterns for internal emails)
  const extractDomain = (email: string | undefined): string | undefined => {
    if (!email || !email.includes('@')) return undefined;
    // First extract email from angle brackets if present
    const match = email.match(/<([^>]+@[^>]+)>/);
    const cleanEmail = match ? match[1] : email;
    if (!cleanEmail.includes('@')) return undefined;
    const domain = cleanEmail.split('@')[1]?.toLowerCase();
    // Don't return internal Bensley domains - shouldn't create domain patterns for internal emails
    if (domain && INTERNAL_DOMAINS.includes(domain)) return undefined;
    return domain;
  };

  const domain = extractDomain(senderEmail);
  const isBensleyInternal = isInternalEmail(senderEmail);

  const handleAddTag = (tag: string) => {
    const normalizedTag = tag.toLowerCase().trim();
    if (normalizedTag && !userContext.tags.includes(normalizedTag)) {
      onChange({
        ...userContext,
        tags: [...userContext.tags, normalizedTag],
      });
    }
    setTagInput("");
    setShowTagSuggestions(false);
  };

  const handleRemoveTag = (tag: string) => {
    onChange({
      ...userContext,
      tags: userContext.tags.filter(t => t !== tag),
    });
  };

  const handleTagInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      handleAddTag(tagInput);
    }
  };

  const filteredTagSuggestions = availableTags.filter(
    t => t.tag_name.toLowerCase().includes(tagInput.toLowerCase()) &&
         !userContext.tags.includes(t.tag_name)
  ).slice(0, 5);

  return (
    <div className="space-y-4">
      {/* Context Notes */}
      <div className="space-y-2">
        <Label htmlFor="context-notes" className="text-xs text-slate-500">
          Context Notes
        </Label>
        <Textarea
          id="context-notes"
          placeholder="Add any notes or context about this suggestion..."
          value={userContext.notes}
          onChange={(e) => onChange({ ...userContext, notes: e.target.value })}
          className="h-20 text-sm resize-none"
        />
      </div>

      {/* Tags */}
      <div className="space-y-2">
        <Label className="text-xs text-slate-500">Tags</Label>
        <div className="flex flex-wrap gap-1 mb-2">
          {userContext.tags.map((tag) => (
            <Badge
              key={tag}
              variant="secondary"
              className="text-xs cursor-pointer hover:bg-slate-200"
              onClick={() => handleRemoveTag(tag)}
            >
              {tag}
              <X className="h-3 w-3 ml-1" />
            </Badge>
          ))}
        </div>
        <div className="relative">
          <Input
            placeholder="Add tags..."
            value={tagInput}
            onChange={(e) => {
              setTagInput(e.target.value);
              setShowTagSuggestions(e.target.value.length > 0);
            }}
            onKeyDown={handleTagInputKeyDown}
            onFocus={() => setShowTagSuggestions(tagInput.length > 0)}
            onBlur={() => setTimeout(() => setShowTagSuggestions(false), 200)}
            className="text-sm"
          />
          {showTagSuggestions && filteredTagSuggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-md shadow-lg z-10">
              {filteredTagSuggestions.map((tag) => (
                <button
                  key={tag.tag_id}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-50 flex items-center justify-between"
                  onClick={() => handleAddTag(tag.tag_name)}
                >
                  <span>{tag.tag_name}</span>
                  <span className="text-xs text-slate-400">{tag.tag_category}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Contact Role (only for contact suggestions) */}
      {suggestionType === 'new_contact' && (
        <div className="space-y-2">
          <Label className="text-xs text-slate-500">Contact Role</Label>
          <Select
            value={userContext.contact_role || ""}
            onValueChange={(v) => onChange({ ...userContext, contact_role: v || undefined })}
          >
            <SelectTrigger className="text-sm">
              <SelectValue placeholder="Select role..." />
            </SelectTrigger>
            <SelectContent>
              {CONTACT_ROLES.map((role) => (
                <SelectItem key={role.value} value={role.value}>
                  {role.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Priority */}
      <div className="space-y-2">
        <Label className="text-xs text-slate-500">Priority</Label>
        <div className="flex gap-2">
          {PRIORITIES.map((priority) => (
            <Badge
              key={priority.value}
              variant="outline"
              className={`cursor-pointer transition-all ${
                userContext.priority === priority.value
                  ? priority.color
                  : 'bg-white text-slate-500 hover:bg-slate-50'
              }`}
              onClick={() => onChange({
                ...userContext,
                priority: userContext.priority === priority.value ? undefined : priority.value
              })}
            >
              {priority.label}
            </Badge>
          ))}
        </div>
      </div>

      {/* Pattern Learning Options */}
      {showPatternOptions && (
        <div className="space-y-3 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
          <Label className="text-xs text-emerald-800 font-semibold">
            Learn from this approval
          </Label>

          {/* Don't show sender pattern option for internal Bensley employees */}
          {senderEmail && !isBensleyInternal && (
            <div className="flex items-center gap-2">
              <Checkbox
                id="sender-pattern"
                checked={createSenderPattern}
                onCheckedChange={(checked) => onSenderPatternChange?.(checked === true)}
              />
              <Label htmlFor="sender-pattern" className="text-sm text-emerald-700 cursor-pointer">
                Always link emails from <code className="bg-emerald-100 px-1 rounded text-xs">{senderEmail}</code> to this project
              </Label>
            </div>
          )}

          {/* Show a note if this is an internal Bensley email */}
          {senderEmail && isBensleyInternal && (
            <p className="text-xs text-slate-500 italic">
              Pattern learning disabled for Bensley staff emails
            </p>
          )}

          {domain && (
            <div className="flex items-center gap-2">
              <Checkbox
                id="domain-pattern"
                checked={createDomainPattern}
                onCheckedChange={(checked) => onDomainPatternChange?.(checked === true)}
              />
              <Label htmlFor="domain-pattern" className="text-sm text-emerald-700 cursor-pointer">
                Always link emails from <code className="bg-emerald-100 px-1 rounded text-xs">@{domain}</code> to this project
              </Label>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
