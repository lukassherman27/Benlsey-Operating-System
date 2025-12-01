"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Calendar, Video, DollarSign, ChevronRight, CalendarDays } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import Link from "next/link";
import { format, addDays, isSameDay, parseISO } from "date-fns";

interface CalendarEvent {
  type: "meeting" | "invoice" | "milestone";
  title: string;
  time?: string;
  amount?: number;
  date: Date;
}

export function CalendarWidget() {
  // Fetch upcoming meetings
  const meetingsQuery = useQuery({
    queryKey: ["dashboard-meetings"],
    queryFn: api.getDashboardMeetings,
    staleTime: 1000 * 60 * 5,
  });

  // Fetch unpaid invoices to show on calendar
  const invoicesQuery = useQuery({
    queryKey: ["invoices-due-soon"],
    queryFn: () => api.getOldestUnpaidInvoices(10),
    staleTime: 1000 * 60 * 10,
  });

  // Generate next 7 days
  const today = new Date();
  const next7Days = Array.from({ length: 7 }, (_, i) => addDays(today, i));

  // Collect all events
  const events: CalendarEvent[] = [];

  // Add meetings
  if (meetingsQuery.data?.meetings) {
    meetingsQuery.data.meetings.forEach((meeting: Record<string, unknown>) => {
      const startTime = meeting.start_time as string;
      if (startTime) {
        try {
          const meetingDate = parseISO(startTime);
          events.push({
            type: "meeting",
            title: (meeting.title as string) || (meeting.subject as string) || "Meeting",
            time: format(meetingDate, "h:mm a"),
            date: meetingDate,
          });
        } catch {
          // Skip invalid dates
        }
      }
    });
  }

  // Add invoice due dates
  if (invoicesQuery.data?.invoices) {
    invoicesQuery.data.invoices
      .filter((inv: Record<string, unknown>) => {
        const dueDate = inv.due_date as string;
        if (!dueDate) return false;
        try {
          const due = parseISO(dueDate);
          return due >= today && due <= addDays(today, 7);
        } catch {
          return false;
        }
      })
      .forEach((inv: Record<string, unknown>) => {
        try {
          const dueDate = parseISO(inv.due_date as string);
          events.push({
            type: "invoice",
            title: `Invoice ${inv.invoice_number} due`,
            amount: (inv.invoice_amount as number) - ((inv.payment_amount as number) || 0),
            date: dueDate,
          });
        } catch {
          // Skip invalid dates
        }
      });
  }

  // Group events by day
  const eventsByDay = next7Days.map((day) => ({
    date: day,
    events: events.filter((e) => isSameDay(e.date, day)),
  }));

  const isLoading = meetingsQuery.isLoading;
  const hasEvents = events.length > 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5 text-teal-600" />
            <h3 className="font-semibold">Upcoming 7 Days</h3>
          </div>
          <Link
            href="/meetings"
            className="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1"
          >
            View Calendar <ChevronRight className="h-3 w-3" />
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="animate-pulse space-y-2">
            <div className="h-16 bg-slate-100 rounded-lg" />
          </div>
        ) : !hasEvents ? (
          <div className="text-center py-6 text-slate-500">
            <Calendar className="h-10 w-10 mx-auto mb-2 text-slate-300" />
            <p className="text-sm">No upcoming events</p>
            <Link
              href="/meetings"
              className="text-xs text-teal-600 hover:underline mt-1 inline-block"
            >
              Add a meeting
            </Link>
          </div>
        ) : (
          <div className="space-y-1">
            {/* Mini calendar strip */}
            <div className="grid grid-cols-7 gap-1 mb-3">
              {eventsByDay.map(({ date, events: dayEvents }) => (
                <DayCell key={date.toISOString()} date={date} events={dayEvents} />
              ))}
            </div>

            {/* Event list for days with events */}
            <div className="space-y-2 max-h-[180px] overflow-y-auto">
              {eventsByDay
                .filter(({ events: dayEvents }) => dayEvents.length > 0)
                .slice(0, 5)
                .map(({ date, events: dayEvents }) => (
                  <div key={date.toISOString()} className="space-y-1">
                    <p className="text-xs font-medium text-slate-500">
                      {format(date, "EEE, MMM d")}
                    </p>
                    {dayEvents.map((event, idx) => (
                      <EventItem key={idx} event={event} />
                    ))}
                  </div>
                ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function DayCell({ date, events }: { date: Date; events: CalendarEvent[] }) {
  const isToday = isSameDay(date, new Date());
  const hasMeetings = events.some((e) => e.type === "meeting");
  const hasInvoices = events.some((e) => e.type === "invoice");

  return (
    <div
      className={cn(
        "text-center p-1 rounded-lg",
        isToday && "bg-teal-50 ring-1 ring-teal-200"
      )}
    >
      <p className={cn("text-xs", isToday ? "font-bold text-teal-700" : "text-slate-500")}>
        {format(date, "EEE")}
      </p>
      <p className={cn("text-sm font-semibold", isToday ? "text-teal-900" : "text-slate-900")}>
        {format(date, "d")}
      </p>
      {events.length > 0 && (
        <div className="flex justify-center gap-0.5 mt-0.5">
          {hasMeetings && <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />}
          {hasInvoices && <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />}
        </div>
      )}
    </div>
  );
}

function EventItem({ event }: { event: CalendarEvent }) {
  const icons = {
    meeting: <Video className="h-3.5 w-3.5 text-blue-600" />,
    invoice: <DollarSign className="h-3.5 w-3.5 text-amber-600" />,
    milestone: <Calendar className="h-3.5 w-3.5 text-purple-600" />,
  };

  const bgColors = {
    meeting: "bg-blue-50 border-blue-100",
    invoice: "bg-amber-50 border-amber-100",
    milestone: "bg-purple-50 border-purple-100",
  };

  return (
    <div className={cn("flex items-center gap-2 p-2 rounded border text-sm", bgColors[event.type])}>
      {icons[event.type]}
      <div className="flex-1 min-w-0">
        <p className="font-medium text-slate-900 truncate text-xs">{event.title}</p>
        {event.time && <p className="text-xs text-slate-500">{event.time}</p>}
      </div>
      {event.amount && (
        <span className="text-xs font-medium text-amber-700">
          {formatCurrency(event.amount)}
        </span>
      )}
    </div>
  );
}
