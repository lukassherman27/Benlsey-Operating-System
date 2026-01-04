/**
 * Auth Layout
 *
 * Simple layout for authentication pages (no sidebar, centered content).
 */

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="min-h-screen w-full bg-transparent">{children}</div>;
}
