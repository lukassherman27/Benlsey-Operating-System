"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
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
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Calendar,
  Clock,
  MapPin,
  Video,
  ChevronRight,
  ChevronDown,
  ExternalLink,
  Plus,
  Loader2,
  FileText,
  CheckCircle2,
} from "lucide-react";
import { format, parseISO, isPast, isFuture, isToday } from "date-fns";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { useState } from "react";

interface Meeting {
  meeting_id: number;
  title: string;
  description: string | null;
  meeting_type: string;
  meeting_date: string;
  start_time: string | null;
  end_time: string | null;
  location: string | null;
  meeting_link: string | null;
  status: string;
  proposal_id: number | null;
  project_code: string | null;
  attendees: string | null;
  created_at: string;
  // Transcript fields (from JOIN)
  transcript_id?: number | null;
  transcript_summary?: string | null;
  transcript_polished_summary?: string | null;
  transcript_key_points?: string | null;
  transcript_action_items?: string | null;
  transcript_duration?: number | null;
}

interface ProposalMeetingsProps {
  projectCode: string;
}

const meetingTypeColors: Record<string, string> = {
  client_call: "bg-blue-100 text-blue-700 border-blue-200",
  client_meeting: "bg-blue-100 text-blue-700 border-blue-200",
  internal: "bg-slate-100 text-slate-700 border-slate-200",
  presentation: "bg-purple-100 text-purple-700 border-purple-200",
  review: "bg-amber-100 text-amber-700 border-amber-200",
  site_visit: "bg-emerald-100 text-emerald-700 border-emerald-200",
  contract_negotiation: "bg-green-100 text-green-700 border-green-200",
};

export function ProposalMeetings({ projectCode }: ProposalMeetingsProps) {
  const queryClient = useQueryClient();
  const [showPast, setShowPast] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [formData, setFormData] = useState({
    title: "",
    meeting_type: "client_call",
    meeting_date: "",
    start_time: "",
    location: "",
    meeting_link: "",
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["project-meetings", projectCode],
    queryFn: () => api.getProjectMeetings(projectCode),
    enabled: !!projectCode,
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: () => api.createMeeting({
      ...formData,
      project_code: projectCode,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-meetings", projectCode] });
      setShowCreateModal(false);
      setFormData({
        title: "",
        meeting_type: "client_call",
        meeting_date: "",
        start_time: "",
        location: "",
        meeting_link: "",
      });
    },
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent className="space-y-2">
          {[1, 2].map((i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return null;
  }

  const meetings = (data?.meetings || []) as Meeting[];

  // Separate upcoming and past/completed meetings
  // If status is "completed", always show in past even if today's date
  const upcomingMeetings = meetings.filter((m) => {
    if (m.status === 'completed') return false; // Completed meetings go to past
    const meetingDate = parseISO(m.meeting_date);
    return isFuture(meetingDate) || isToday(meetingDate);
  }).sort((a, b) => new Date(a.meeting_date).getTime() - new Date(b.meeting_date).getTime());

  const pastMeetings = meetings.filter((m) => {
    if (m.status === 'completed') return true; // Completed meetings always show here
    const meetingDate = parseISO(m.meeting_date);
    return isPast(meetingDate) && !isToday(meetingDate);
  }).sort((a, b) => new Date(b.meeting_date).getTime() - new Date(a.meeting_date).getTime());

  const getZoomLink = (location: string | null, link: string | null) => {
    if (link) return link;
    if (!location) return null;
    const match = location.match(/https:\/\/[^\s]*(zoom|meet|teams)[^\s]*/i);
    return match ? match[0] : null;
  };

  const formatMeetingTime = (date: string, startTime: string | null) => {
    const dateObj = parseISO(date);
    const dateStr = format(dateObj, "EEE, MMM d");
    if (startTime) {
      const timeStr = startTime.slice(0, 5);
      return `${dateStr} at ${timeStr}`;
    }
    return dateStr;
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const parseJsonField = (field: string | null): any[] => {
    if (!field) return [];
    try {
      const parsed = JSON.parse(field);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  };

  // Extract display text from action item (can be string or object with task field)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getActionItemText = (item: any): string => {
    if (typeof item === 'string') return item;
    if (item && typeof item === 'object' && item.task) return item.task;
    return String(item);
  };

  const MeetingCard = ({ meeting, isUpcoming }: { meeting: Meeting; isUpcoming: boolean }) => {
    const meetingDate = parseISO(meeting.meeting_date);
    const isUpcomingToday = isToday(meetingDate);
    const videoLink = getZoomLink(meeting.location, meeting.meeting_link);
    const hasTranscript = !!meeting.transcript_summary || !!meeting.transcript_polished_summary;
    const hasPolishedSummary = !!meeting.transcript_polished_summary;

    return (
      <div
        onClick={() => setSelectedMeeting(meeting)}
        className={cn(
          "p-3 rounded-lg border transition-colors cursor-pointer",
          isUpcoming && isUpcomingToday
            ? "bg-blue-100 border-blue-300 hover:bg-blue-150"
            : isUpcoming
            ? "bg-white border-blue-100 hover:bg-blue-50"
            : "bg-slate-50 border-slate-100 hover:bg-slate-100"
        )}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
              isUpcoming && isUpcomingToday ? "bg-blue-200" : "bg-blue-50"
            )}>
              {hasTranscript ? (
                <FileText className="h-4 w-4 text-blue-600" />
              ) : (
                <Video className="h-4 w-4 text-blue-600" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">
                {meeting.title}
              </p>
              <div className="flex flex-wrap items-center gap-2 mt-1">
                <span className="text-xs text-slate-600 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatMeetingTime(meeting.meeting_date, meeting.start_time)}
                </span>
                {hasPolishedSummary ? (
                  <Badge className="bg-emerald-100 text-emerald-700 text-xs">
                    Full Notes
                  </Badge>
                ) : hasTranscript ? (
                  <Badge className="bg-purple-100 text-purple-700 text-xs">
                    Has Notes
                  </Badge>
                ) : null}
              </div>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            {isUpcoming && isUpcomingToday && (
              <Badge className="bg-blue-600 text-white text-xs">Today</Badge>
            )}
            {videoLink && isUpcoming && (
              <Button
                size="sm"
                variant="outline"
                className="text-xs text-blue-600 border-blue-300 h-6 px-2"
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(videoLink, '_blank');
                }}
              >
                <ExternalLink className="h-3 w-3 mr-1" /> Join
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      <Card className="border-blue-200 bg-gradient-to-br from-blue-50/50 to-indigo-50/30">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center justify-between text-base">
            <div className="flex items-center gap-2 text-blue-800">
              <Calendar className="h-4 w-4" />
              <span>Meetings ({meetings.length})</span>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowCreateModal(true)}
                className="text-blue-700 hover:text-blue-900 hover:bg-blue-100 h-7 w-7 p-0"
                title="Schedule new meeting"
              >
                <Plus className="h-4 w-4" />
              </Button>
              <Link href="/meetings">
                <Button variant="ghost" size="sm" className="text-xs text-blue-700 hover:text-blue-900">
                  Calendar <ChevronRight className="h-3 w-3 ml-1" />
                </Button>
              </Link>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Upcoming Meetings */}
          {upcomingMeetings.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-blue-700 uppercase tracking-wider">
                Upcoming ({upcomingMeetings.length})
              </p>
              {upcomingMeetings.slice(0, 3).map((meeting) => (
                <MeetingCard key={meeting.meeting_id} meeting={meeting} isUpcoming={true} />
              ))}
              {upcomingMeetings.length > 3 && (
                <p className="text-xs text-center text-muted-foreground">
                  +{upcomingMeetings.length - 3} more upcoming
                </p>
              )}
            </div>
          )}

          {/* Past Meetings */}
          {pastMeetings.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-blue-100">
              <button
                onClick={() => setShowPast(!showPast)}
                className="flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-700 transition-colors w-full"
              >
                {showPast ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                Past Meetings ({pastMeetings.length})
              </button>
              {showPast && (
                <div className="space-y-2">
                  {pastMeetings.slice(0, 5).map((meeting) => (
                    <MeetingCard key={meeting.meeting_id} meeting={meeting} isUpcoming={false} />
                  ))}
                  {pastMeetings.length > 5 && (
                    <p className="text-xs text-center text-muted-foreground">
                      +{pastMeetings.length - 5} more past meetings
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Empty State */}
          {meetings.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">
              No meetings scheduled. Click + to add one.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Meeting Detail Modal */}
      <Dialog open={!!selectedMeeting} onOpenChange={(open) => !open && setSelectedMeeting(null)}>
        <DialogContent className="max-w-2xl max-h-[85vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedMeeting?.title}
              {selectedMeeting?.transcript_summary && (
                <Badge className="bg-purple-100 text-purple-700">
                  <FileText className="h-3 w-3 mr-1" /> Has Meeting Notes
                </Badge>
              )}
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-[60vh]">
            {selectedMeeting && (
              <div className="space-y-4 pr-4">
                {/* Meeting Info */}
                <div className="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-lg">
                  <div>
                    <p className="text-xs font-medium text-slate-500 uppercase">Date</p>
                    <p className="text-sm text-slate-900">
                      {format(parseISO(selectedMeeting.meeting_date), "EEEE, MMMM d, yyyy")}
                    </p>
                  </div>
                  {selectedMeeting.start_time && (
                    <div>
                      <p className="text-xs font-medium text-slate-500 uppercase">Time</p>
                      <p className="text-sm text-slate-900">
                        {selectedMeeting.start_time.slice(0, 5)}
                        {selectedMeeting.end_time && ` - ${selectedMeeting.end_time.slice(0, 5)}`}
                      </p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs font-medium text-slate-500 uppercase">Type</p>
                    <Badge variant="outline" className={cn("text-xs", meetingTypeColors[selectedMeeting.meeting_type])}>
                      {selectedMeeting.meeting_type?.replace(/_/g, " ")}
                    </Badge>
                  </div>
                  {selectedMeeting.location && (
                    <div>
                      <p className="text-xs font-medium text-slate-500 uppercase">Location</p>
                      <p className="text-sm text-slate-900 flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {selectedMeeting.location}
                      </p>
                    </div>
                  )}
                </div>

                {/* Polished Summary (preferred) or Transcript Summary */}
                {(selectedMeeting.transcript_polished_summary || selectedMeeting.transcript_summary) && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-emerald-800 flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      {selectedMeeting.transcript_polished_summary ? "Meeting Notes" : "Meeting Summary"}
                      {selectedMeeting.transcript_polished_summary && (
                        <Badge className="bg-emerald-100 text-emerald-700 text-xs">Full Notes</Badge>
                      )}
                    </h3>
                    <div className={cn(
                      "p-4 rounded-lg border",
                      selectedMeeting.transcript_polished_summary
                        ? "bg-slate-50 border-slate-200"
                        : "bg-purple-50 border-purple-100"
                    )}>
                      <div className="text-sm text-slate-700 whitespace-pre-wrap font-mono leading-relaxed">
                        {selectedMeeting.transcript_polished_summary || selectedMeeting.transcript_summary}
                      </div>
                    </div>

                    {/* Key Points - only show if no polished summary */}
                    {!selectedMeeting.transcript_polished_summary && selectedMeeting.transcript_key_points && (
                      <div>
                        <h4 className="text-xs font-semibold text-purple-700 uppercase mb-2">Key Points</h4>
                        <ul className="space-y-1">
                          {parseJsonField(selectedMeeting.transcript_key_points).map((point, i) => (
                            <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                              <span className="text-purple-400 mt-1">•</span>
                              <span>{point}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Action Items - only show if no polished summary */}
                    {!selectedMeeting.transcript_polished_summary && selectedMeeting.transcript_action_items && (
                      <div>
                        <h4 className="text-xs font-semibold text-purple-700 uppercase mb-2">Action Items</h4>
                        <ul className="space-y-1">
                          {parseJsonField(selectedMeeting.transcript_action_items).map((item, i) => (
                            <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                              <CheckCircle2 className="h-4 w-4 text-purple-400 mt-0.5 flex-shrink-0" />
                              <span>{getActionItemText(item)}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* No transcript message */}
                {!selectedMeeting.transcript_summary && !selectedMeeting.transcript_polished_summary && isPast(parseISO(selectedMeeting.meeting_date)) && (
                  <div className="p-4 bg-amber-50 rounded-lg border border-amber-100">
                    <p className="text-sm text-amber-700">
                      No meeting notes recorded yet. To add notes, go to the{" "}
                      <Link href="/transcripts" className="underline font-medium">
                        Transcripts page
                      </Link>{" "}
                      and paste your meeting summary.
                    </p>
                  </div>
                )}
              </div>
            )}
          </ScrollArea>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedMeeting(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Meeting Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Schedule Meeting</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="title">Meeting Title *</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="e.g., Client call with John"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="date">Date *</Label>
                <Input
                  id="date"
                  type="date"
                  value={formData.meeting_date}
                  onChange={(e) => setFormData({ ...formData, meeting_date: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="time">Time</Label>
                <Input
                  id="time"
                  type="time"
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Meeting Type</Label>
              <Select
                value={formData.meeting_type}
                onValueChange={(v) => setFormData({ ...formData, meeting_type: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="client_call">Client Call</SelectItem>
                  <SelectItem value="client_meeting">Client Meeting</SelectItem>
                  <SelectItem value="presentation">Presentation</SelectItem>
                  <SelectItem value="site_visit">Site Visit</SelectItem>
                  <SelectItem value="internal">Internal</SelectItem>
                  <SelectItem value="review">Review</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="location">Location / Meeting Link</Label>
              <Input
                id="location"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                placeholder="e.g., Zoom, Office, or paste meeting URL"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending || !formData.title || !formData.meeting_date}
            >
              {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Meeting
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
