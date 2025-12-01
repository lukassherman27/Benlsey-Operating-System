"use client";

import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Database, ArrowRight, Plus, Pencil, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { SuggestedAction } from "@/lib/types";

interface FieldChange {
  field: string;
  old_value: string | number | null;
  new_value: string | number | null;
}

interface DatabasePreviewProps {
  action: 'insert' | 'update' | 'delete' | 'none';
  table: string;
  summary: string;
  changes: FieldChange[];
  selectedActions?: SuggestedAction[];
}

export function DatabasePreview({
  action,
  table,
  summary,
  changes,
  selectedActions = [],
}: DatabasePreviewProps) {
  const getActionIcon = () => {
    switch (action) {
      case 'insert': return <Plus className="h-4 w-4" />;
      case 'update': return <Pencil className="h-4 w-4" />;
      case 'delete': return <Trash2 className="h-4 w-4" />;
      default: return <Database className="h-4 w-4" />;
    }
  };

  const getActionColor = () => {
    switch (action) {
      case 'insert': return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 'update': return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'delete': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Database className="h-4 w-4 text-slate-500" />
        <Label className="text-xs text-slate-500 font-semibold">Database Changes</Label>
      </div>

      {/* Action Badge */}
      <div className="flex items-center gap-2">
        <Badge variant="outline" className={cn("text-xs", getActionColor())}>
          {getActionIcon()}
          <span className="ml-1 capitalize">{action}</span>
        </Badge>
        <code className="text-xs bg-slate-100 px-2 py-0.5 rounded text-slate-700">
          {table}
        </code>
      </div>

      {/* Summary */}
      <p className="text-sm text-slate-700">{summary}</p>

      {/* Field Changes */}
      {changes.length > 0 && (
        <div className="space-y-2 mt-3">
          <Label className="text-xs text-slate-400">Field Changes</Label>
          <div className="space-y-1">
            {changes.map((change, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 p-2 bg-slate-50 rounded text-xs font-mono"
              >
                <span className="text-slate-600 min-w-[100px]">{change.field}</span>
                <span className="text-red-500 line-through">
                  {formatValue(change.old_value)}
                </span>
                <ArrowRight className="h-3 w-3 text-slate-400 shrink-0" />
                <span className="text-emerald-600">
                  {formatValue(change.new_value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Additional Actions */}
      {selectedActions.length > 0 && (
        <div className="space-y-2 mt-3 pt-3 border-t">
          <Label className="text-xs text-slate-400">Additional Actions</Label>
          <div className="space-y-1">
            {selectedActions.map((action) => (
              <div
                key={action.id}
                className="p-2 bg-blue-50 rounded text-xs text-blue-700 font-mono"
              >
                {action.database_change}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SQL Preview (collapsed by default) */}
      {changes.length > 0 && action !== 'none' && (
        <details className="mt-2">
          <summary className="text-xs text-slate-400 cursor-pointer hover:text-slate-600">
            View SQL
          </summary>
          <pre className="mt-2 p-3 bg-slate-900 text-slate-100 rounded-lg text-xs overflow-x-auto">
            {generateSQL(action, table, changes)}
          </pre>
        </details>
      )}
    </div>
  );
}

function formatValue(value: string | number | null): string {
  if (value === null || value === undefined) return '(empty)';
  if (typeof value === 'string' && value === '') return '(empty)';
  return String(value);
}

function generateSQL(action: 'insert' | 'update' | 'delete' | 'none', table: string, changes: FieldChange[]): string {
  switch (action) {
    case 'insert':
      const fields = changes.map(c => c.field).join(', ');
      const values = changes.map(c => `'${c.new_value}'`).join(', ');
      return `INSERT INTO ${table} (${fields})\nVALUES (${values});`;

    case 'update':
      const setClauses = changes.map(c => `${c.field} = '${c.new_value}'`).join(',\n  ');
      return `UPDATE ${table}\nSET ${setClauses}\nWHERE id = ?;`;

    case 'delete':
      return `DELETE FROM ${table}\nWHERE id = ?;`;

    default:
      return '-- No changes';
  }
}
