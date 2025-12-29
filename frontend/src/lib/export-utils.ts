/**
 * Export Utilities - CSV/Excel export functionality
 */

/**
 * Convert array of objects to CSV string
 */
export function convertToCSV(data: Record<string, unknown>[]): string {
  if (data.length === 0) return "";

  // Get headers from first object
  const headers = Object.keys(data[0]);
  const headerRow = headers.join(",");

  // Convert data rows
  const rows = data.map((row) =>
    headers
      .map((header) => {
        const value = row[header];
        // Handle values that contain commas, quotes, or newlines
        if (
          typeof value === "string" &&
          (value.includes(",") || value.includes('"') || value.includes("\n"))
        ) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value ?? "";
      })
      .join(",")
  );

  return [headerRow, ...rows].join("\n");
}

/**
 * Download CSV file
 */
export function downloadCSV(csvContent: string, filename: string): void {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");

  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
}

/**
 * Export data to CSV file
 */
export function exportToCSV(
  data: Record<string, unknown>[],
  filename: string
): void {
  const csv = convertToCSV(data);
  const timestampedFilename = `${filename}-${new Date().toISOString().split("T")[0]}.csv`;
  downloadCSV(csv, timestampedFilename);
}

/**
 * Format data for export (clean up null/undefined values, format dates, etc.)
 */
export function prepareDataForExport<T extends Record<string, unknown>>(
  data: T[],
  columnMapping?: Record<string, string>
): Record<string, unknown>[] {
  return data.map((row) => {
    const formattedRow: Record<string, unknown> = {};

    Object.entries(row).forEach(([key, value]) => {
      // Use column mapping if provided
      const displayKey = columnMapping?.[key] || key;

      // Format different types of values
      if (value === null || value === undefined) {
        formattedRow[displayKey] = "";
      } else if (value instanceof Date) {
        formattedRow[displayKey] = value.toLocaleDateString();
      } else if (typeof value === "boolean") {
        formattedRow[displayKey] = value ? "Yes" : "No";
      } else {
        formattedRow[displayKey] = value;
      }
    });

    return formattedRow;
  });
}
