"use client";

interface FormattedSummaryProps {
  content: string;
}

/**
 * Parses and formats a meeting summary that was stored without line breaks.
 * Detects section headers, emoji bullets, tables, and other structure.
 */
export function FormattedSummary({ content }: FormattedSummaryProps) {
  // Format the content with intelligent line breaks
  const formatContent = (text: string): string => {
    let formatted = text;

    // Add line breaks before emoji headers
    formatted = formatted.replace(/([^\n])([📋📝✅🔧🏨📍🎯💰📊🗓️⏰📌🔑💡📞📧🏗️🎨👥💼📄🔗⚡️🌟🎉🚀⚠️❌❓])/g, '$1\n\n$2');

    // Add line breaks before common headers
    const headers = [
      'Date & Time',
      'Platform',
      'Attendees',
      'Meeting Summary:',
      'Key Points',
      'Action Items',
      'Next Steps',
      'Immediate:',
      'Technical',
      'Notes',
      'Decisions',
      'NEW PROJECT',
      'BENSLEY Action',
      'PEARL RESORTS',
      'Minutes prepared',
      'Projects:',
      'Client:',
    ];

    headers.forEach(header => {
      const regex = new RegExp(`([^\\n])(${header})`, 'g');
      formatted = formatted.replace(regex, '$1\n\n$2');
    });

    // Add line breaks before numbered project listings
    formatted = formatted.replace(/([^\n])(\d+\.\s+[A-Z][a-zA-Z\s']+(?:Hotel|Resort|Island|Project|Type|Size|Status|Vision|Research|Note))/g, '$1\n$2');

    // Add line breaks before Type:, Size:, Status:, Vision:, etc.
    formatted = formatted.replace(/([^\n])((?:Type|Size|Status|Vision|Research|Note|Land|Terrain|Concept|Existing Site|Opportunity):\s)/g, '$1\n$2');

    // Handle table-like content (# Item Status Notes)
    formatted = formatted.replace(/([^\n])(#\s+Item\s+Status\s+Notes)/g, '$1\n\n$2');
    formatted = formatted.replace(/(Notes)(\s+\d+\s+)/g, '$1\n$2');

    // Add line breaks after table headers and before each numbered row
    formatted = formatted.replace(/(\d)\s+(\d+)\s+([A-Z])/g, '$1\n$2 $3');

    // Clean up multiple spaces
    formatted = formatted.replace(/  +/g, ' ');

    // Clean up multiple newlines (max 2)
    formatted = formatted.replace(/\n{3,}/g, '\n\n');

    return formatted.trim();
  };

  const formattedContent = formatContent(content);
  const lines = formattedContent.split('\n');

  return (
    <div className="space-y-2">
      {lines.map((line, index) => {
        const trimmedLine = line.trim();

        if (!trimmedLine) {
          return <div key={index} className="h-2" />;
        }

        // Emoji section headers - make them bold and larger
        if (/^[📋📝✅🔧🏨📍🎯💰📊🗓️⏰📌🔑💡📞📧🏗️🎨👥💼📄🔗⚡️🌟🎉🚀⚠️❌❓]/.test(trimmedLine)) {
          return (
            <h3 key={index} className="text-base font-semibold text-slate-800 mt-4 mb-2 flex items-center gap-2">
              {trimmedLine}
            </h3>
          );
        }

        // Main title (first line, usually project name)
        if (index === 0 && trimmedLine.length > 20) {
          return (
            <h2 key={index} className="text-lg font-bold text-slate-900 mb-3 pb-2 border-b border-slate-200">
              {trimmedLine}
            </h2>
          );
        }

        // Date & Time, Platform, Attendees - metadata style
        if (/^(Date & Time|Platform|Attendees)\s/.test(trimmedLine)) {
          const [label, ...rest] = trimmedLine.split(/(?<=Date & Time|Platform|Attendees)\s/);
          return (
            <div key={index} className="flex gap-2 text-sm">
              <span className="font-medium text-slate-600 min-w-[100px]">{label}</span>
              <span className="text-slate-700">{rest.join(' ')}</span>
            </div>
          );
        }

        // Meeting Summary paragraph
        if (/^Meeting Summary:/.test(trimmedLine)) {
          const summaryText = trimmedLine.replace('Meeting Summary:', '').trim();
          return (
            <div key={index} className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
              <span className="font-semibold text-slate-700">Meeting Summary: </span>
              <span className="text-slate-600">{summaryText}</span>
            </div>
          );
        }

        // NEW PROJECT callout
        if (/^NEW PROJECT/.test(trimmedLine)) {
          return (
            <div key={index} className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <span className="font-bold text-amber-800">{trimmedLine}</span>
            </div>
          );
        }

        // Numbered items (1. Something)
        if (/^\d+\.\s+[A-Z]/.test(trimmedLine)) {
          return (
            <div key={index} className="font-medium text-slate-800 mt-3">
              {trimmedLine}
            </div>
          );
        }

        // Type:, Status:, etc. - sub-details
        if (/^(Type|Size|Status|Vision|Research|Note|Land|Terrain|Concept|Existing Site|Opportunity):/.test(trimmedLine)) {
          const colonIndex = trimmedLine.indexOf(':');
          const label = trimmedLine.substring(0, colonIndex + 1);
          const value = trimmedLine.substring(colonIndex + 1).trim();
          return (
            <div key={index} className="flex gap-2 text-sm ml-4">
              <span className="font-medium text-slate-500 min-w-[80px]">{label}</span>
              <span className="text-slate-600">{value}</span>
            </div>
          );
        }

        // Action items with checkmarks or BENSLEY/PEARL RESORTS headers
        if (/^(BENSLEY|PEARL RESORTS)/.test(trimmedLine)) {
          return (
            <h4 key={index} className="text-sm font-semibold text-slate-700 mt-4 uppercase tracking-wide">
              {trimmedLine}
            </h4>
          );
        }

        // Table header
        if (/^#\s+Item\s+Status/.test(trimmedLine)) {
          return (
            <div key={index} className="text-xs font-medium text-slate-500 mt-3 p-2 bg-slate-100 rounded">
              {trimmedLine}
            </div>
          );
        }

        // Minutes/footer
        if (/^Minutes prepared|^Projects:|^Client:|^BENSLEY Design/.test(trimmedLine)) {
          return (
            <div key={index} className="text-xs text-slate-400 mt-4 pt-3 border-t border-slate-200">
              {trimmedLine}
            </div>
          );
        }

        // Default line
        return (
          <p key={index} className="text-sm text-slate-700 leading-relaxed">
            {trimmedLine}
          </p>
        );
      })}
    </div>
  );
}
