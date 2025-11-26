"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { PropsWithChildren, useState } from "react";
import { toast } from "sonner";

export function Providers({ children }: PropsWithChildren) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Performance: Cache data for 5 minutes before considering it stale
            staleTime: 1000 * 60 * 5,
            // Performance: Keep unused data in cache for 10 minutes
            gcTime: 1000 * 60 * 10,
            // Don't refetch on window focus to reduce unnecessary API calls
            refetchOnWindowFocus: false,
            // Resilience: Retry failed requests up to 3 times with exponential backoff
            retry: (failureCount, error) => {
              // Don't retry on 4xx errors (client errors)
              if (error instanceof Error && 'status' in error) {
                const status = (error as { status?: number }).status;
                if (status && status >= 400 && status < 500) {
                  return false;
                }
              }
              // Retry up to 3 times for network errors or 5xx errors
              return failureCount < 3;
            },
            // Resilience: Exponential backoff (1s, 2s, 4s)
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
          },
          mutations: {
            // Error Handling: Show toast on mutation errors
            onError: (error) => {
              const message = error instanceof Error ? error.message : "An error occurred";
              toast.error(message);
            },
            // Resilience: Retry mutations once after 1 second
            retry: 1,
            retryDelay: 1000,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
