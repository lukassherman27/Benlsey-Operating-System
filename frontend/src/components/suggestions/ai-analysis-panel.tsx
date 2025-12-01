"use client";

import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Building2,
  DollarSign,
  User,
  Calendar,
  Tag,
  Sparkles,
  Info,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { AIAnalysis, SuggestedAction } from "@/lib/types";

interface AIAnalysisPanelProps {
  analysis: AIAnalysis;
  selectedActions: Set<string>;
  onToggleAction: (actionId: string) => void;
}

export function AIAnalysisPanel({
  analysis,
  selectedActions,
  onToggleAction,
}: AIAnalysisPanelProps) {
  const { detected_entities, suggested_actions, pattern_to_learn, overall_confidence } = analysis;
  const confidencePercent = Math.round(overall_confidence * 100);

  return (
    <div className="space-y-4">
      {/* Overall Confidence */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="text-xs text-slate-500">AI Confidence</Label>
          <span className={cn(
            "text-sm font-medium",
            confidencePercent >= 80 ? "text-emerald-600" :
            confidencePercent >= 50 ? "text-amber-600" : "text-red-600"
          )}>
            {confidencePercent}%
          </span>
        </div>
        <Progress
          value={confidencePercent}
          className={cn(
            "h-2",
            confidencePercent >= 80 ? "[&>div]:bg-emerald-500" :
            confidencePercent >= 50 ? "[&>div]:bg-amber-500" : "[&>div]:bg-red-500"
          )}
        />
      </div>

      {/* Detected Entities */}
      <div className="space-y-3">
        <Label className="text-xs text-slate-500 font-semibold">Detected Entities</Label>

        {/* Projects */}
        {detected_entities.projects.length > 0 && (
          <div className="flex items-start gap-2">
            <Building2 className="h-4 w-4 text-purple-500 mt-0.5 shrink-0" />
            <div className="flex flex-wrap gap-1">
              {detected_entities.projects.map((project, i) => (
                <Badge key={i} variant="outline" className="text-xs bg-purple-50 text-purple-700 border-purple-200">
                  {project}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Fees */}
        {detected_entities.fees.length > 0 && (
          <div className="flex items-start gap-2">
            <DollarSign className="h-4 w-4 text-emerald-500 mt-0.5 shrink-0" />
            <div className="flex flex-wrap gap-1">
              {detected_entities.fees.map((fee, i) => (
                <Badge key={i} variant="outline" className="text-xs bg-emerald-50 text-emerald-700 border-emerald-200">
                  {fee.currency} {fee.amount.toLocaleString()}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Contacts */}
        {detected_entities.contacts.length > 0 && (
          <div className="flex items-start gap-2">
            <User className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
            <div className="flex flex-wrap gap-1">
              {detected_entities.contacts.map((contact, i) => (
                <Badge key={i} variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                  {contact.name || contact.email}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Dates */}
        {detected_entities.dates.length > 0 && (
          <div className="flex items-start gap-2">
            <Calendar className="h-4 w-4 text-orange-500 mt-0.5 shrink-0" />
            <div className="flex flex-wrap gap-1">
              {detected_entities.dates.map((date, i) => (
                <Badge key={i} variant="outline" className="text-xs bg-orange-50 text-orange-700 border-orange-200">
                  {date}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Keywords */}
        {detected_entities.keywords.length > 0 && (
          <div className="flex items-start gap-2">
            <Tag className="h-4 w-4 text-slate-500 mt-0.5 shrink-0" />
            <div className="flex flex-wrap gap-1">
              {detected_entities.keywords.slice(0, 5).map((keyword, i) => (
                <Badge key={i} variant="outline" className="text-xs">
                  {keyword}
                </Badge>
              ))}
              {detected_entities.keywords.length > 5 && (
                <Badge variant="outline" className="text-xs text-slate-400">
                  +{detected_entities.keywords.length - 5} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Empty state */}
        {detected_entities.projects.length === 0 &&
         detected_entities.fees.length === 0 &&
         detected_entities.contacts.length === 0 &&
         detected_entities.dates.length === 0 &&
         detected_entities.keywords.length === 0 && (
          <p className="text-xs text-slate-400 italic">No entities detected</p>
        )}
      </div>

      {/* Suggested Actions */}
      {suggested_actions.length > 0 && (
        <div className="space-y-3">
          <Label className="text-xs text-slate-500 font-semibold">Actions to Apply</Label>
          <div className="space-y-2">
            {suggested_actions.map((action) => (
              <ActionCheckbox
                key={action.id}
                action={action}
                checked={selectedActions.has(action.id)}
                onCheckedChange={() => onToggleAction(action.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Pattern to Learn */}
      {pattern_to_learn && (
        <div className="p-3 bg-blue-50 rounded-lg border border-blue-200 space-y-2">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-blue-600" />
            <Label className="text-xs text-blue-800 font-semibold">Pattern to Learn</Label>
          </div>
          <p className="text-xs text-blue-700">
            {pattern_to_learn.type === 'sender_to_project' && (
              <>Emails from <code className="bg-blue-100 px-1 rounded">{pattern_to_learn.pattern_key}</code> will be linked to <code className="bg-blue-100 px-1 rounded">{pattern_to_learn.target}</code></>
            )}
            {pattern_to_learn.type === 'domain_to_project' && (
              <>Emails from domain <code className="bg-blue-100 px-1 rounded">{pattern_to_learn.pattern_key}</code> will be linked to <code className="bg-blue-100 px-1 rounded">{pattern_to_learn.target}</code></>
            )}
            {pattern_to_learn.type === 'keyword_to_project' && (
              <>Emails containing <code className="bg-blue-100 px-1 rounded">{pattern_to_learn.pattern_key}</code> will be linked to <code className="bg-blue-100 px-1 rounded">{pattern_to_learn.target}</code></>
            )}
          </p>
          <p className="text-xs text-blue-500">
            +{Math.round(pattern_to_learn.confidence_boost * 100)}% confidence boost for future matches
          </p>
        </div>
      )}
    </div>
  );
}

function ActionCheckbox({
  action,
  checked,
  onCheckedChange,
}: {
  action: SuggestedAction;
  checked: boolean;
  onCheckedChange: () => void;
}) {
  const getActionIcon = (type: string) => {
    switch (type) {
      case 'link_email': return '📧';
      case 'update_fee': return '💰';
      case 'link_contact': return '👤';
      case 'learn_pattern': return '🧠';
      default: return '📝';
    }
  };

  return (
    <div className="flex items-start gap-3 p-2 rounded-lg hover:bg-slate-50 transition-colors">
      <Checkbox
        id={action.id}
        checked={checked}
        onCheckedChange={onCheckedChange}
        className="mt-0.5"
      />
      <div className="flex-1 min-w-0">
        <Label
          htmlFor={action.id}
          className="text-sm text-slate-700 cursor-pointer"
        >
          <span className="mr-1">{getActionIcon(action.type)}</span>
          {action.description}
        </Label>
        <p className="text-xs text-slate-400 mt-0.5 font-mono">
          {action.database_change}
        </p>
      </div>
    </div>
  );
}
