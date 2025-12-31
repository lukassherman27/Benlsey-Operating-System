"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Mic, Square, Pause, Play, Check, AlertCircle, Loader2, Clock, Users, Briefcase, X, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface Project { id: number; project_code: string; project_name: string; type: string; }
interface RecordingResult {
  success: boolean; transcript_id: number; audio_path: string; word_count: number;
  summary: string; key_points: string[];
  action_items: Array<{ task: string; assignee: string | null; due_date: string | null; priority: string; }>;
  task_ids: number[]; tasks_created: number;
}

type RecordingState = "idle" | "recording" | "paused" | "processing" | "complete" | "error";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function useMediaRecorder() {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const [isSupported, setIsSupported] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setIsSupported(false);
      setError("Your browser doesn't support audio recording");
    }
  }, []);

  const startRecording = useCallback(async (): Promise<boolean> => {
    try {
      setError(null);
      chunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 44100 }
      });
      streamRef.current = stream;
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus") ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/mp4";
      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.start(1000);
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to start recording";
      setError(message.includes("Permission") ? "Microphone access denied." : message);
      return false;
    }
  }, []);

  const stopRecording = useCallback((): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder) { reject(new Error("No recording")); return; }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        if (streamRef.current) { streamRef.current.getTracks().forEach(t => t.stop()); streamRef.current = null; }
        resolve(blob);
      };
      recorder.onerror = () => reject(new Error("Recording error"));
      recorder.stop();
    });
  }, []);

  const pauseRecording = useCallback(() => { mediaRecorderRef.current?.state === "recording" && mediaRecorderRef.current.pause(); }, []);
  const resumeRecording = useCallback(() => { mediaRecorderRef.current?.state === "paused" && mediaRecorderRef.current.resume(); }, []);

  return { isSupported, error, startRecording, stopRecording, pauseRecording, resumeRecording };
}

function RecordingTimer({ startTime }: { startTime: Date | null }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!startTime) { setElapsed(0); return; }
    const interval = setInterval(() => setElapsed(Math.floor((Date.now() - startTime.getTime()) / 1000)), 1000);
    return () => clearInterval(interval);
  }, [startTime]);
  const format = (n: number) => n.toString().padStart(2, "0");
  const h = Math.floor(elapsed / 3600), m = Math.floor((elapsed % 3600) / 60), s = elapsed % 60;
  return (
    <div className="font-mono text-4xl font-bold text-slate-900 tabular-nums">
      {h > 0 && <span>{format(h)}:</span>}<span>{format(m)}</span><span className="animate-pulse">:</span><span>{format(s)}</span>
    </div>
  );
}

function AttendeeInput({ attendees, onAdd, onRemove }: { attendees: string[]; onAdd: (n: string) => void; onRemove: (i: number) => void; }) {
  const [input, setInput] = useState("");
  const handleAdd = () => { const t = input.trim(); if (t && !attendees.includes(t)) { onAdd(t); setInput(""); } };
  return (
    <div className="space-y-3">
      <Label className="flex items-center gap-2"><Users className="h-4 w-4" />Attendees</Label>
      <div className="flex gap-2">
        <Input placeholder="Add attendee..." value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && handleAdd()} className="flex-1" />
        <Button variant="outline" size="icon" onClick={handleAdd} disabled={!input.trim()}><Plus className="h-4 w-4" /></Button>
      </div>
      {attendees.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {attendees.map((name, i) => (
            <Badge key={i} variant="secondary" className="gap-1 px-3 py-1.5">
              {name}<button onClick={() => onRemove(i)} className="ml-1 hover:text-red-500"><X className="h-3 w-3" /></button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

function ResultsView({ result }: { result: RecordingResult }) {
  return (
    <div className="space-y-6">
      {result.summary && <div className="space-y-2"><h4 className="font-semibold text-slate-900">Summary</h4><p className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">{result.summary}</p></div>}
      {result.key_points?.length > 0 && (
        <div className="space-y-2"><h4 className="font-semibold text-slate-900">Key Points</h4>
          <ul className="space-y-1">{result.key_points.map((p, i) => <li key={i} className="text-sm text-slate-600 flex items-start gap-2"><span className="text-teal-500">-</span>{p}</li>)}</ul>
        </div>
      )}
      {result.action_items?.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-semibold text-slate-900 flex items-center gap-2">Action Items<Badge className="bg-teal-100 text-teal-700 border-0">{result.tasks_created} tasks</Badge></h4>
          <div className="space-y-2">
            {result.action_items.map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
                <Check className="h-4 w-4 text-teal-500 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0"><p className="text-sm text-slate-700">{item.task}</p>
                  <div className="flex gap-3 mt-1 text-xs text-slate-500">{item.assignee && <span>Assignee: {item.assignee}</span>}{item.due_date && <span>Due: {item.due_date}</span>}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="flex gap-4 pt-4 border-t border-slate-200">
        <div className="text-center"><div className="text-2xl font-bold text-slate-900">{result.word_count}</div><div className="text-xs text-slate-500">Words</div></div>
        <div className="text-center"><div className="text-2xl font-bold text-slate-900">{result.tasks_created}</div><div className="text-xs text-slate-500">Tasks</div></div>
        <div className="text-center"><div className="text-2xl font-bold text-slate-900">{result.key_points?.length || 0}</div><div className="text-xs text-slate-500">Key Points</div></div>
      </div>
    </div>
  );
}

export function MeetingRecorder() {
  const [state, setState] = useState<RecordingState>("idle");
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [meetingTitle, setMeetingTitle] = useState("");
  const [attendees, setAttendees] = useState<string[]>([]);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [result, setResult] = useState<RecordingResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { isSupported, error: recorderError, startRecording, stopRecording, pauseRecording, resumeRecording } = useMediaRecorder();

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/recordings/projects`).then(res => res.json()).then(data => data.projects && setProjects(data.projects)).catch(console.error);
  }, []);

  const handleStart = async () => { if (await startRecording()) { setState("recording"); setStartTime(new Date()); setResult(null); setErrorMessage(null); } };
  const handlePause = () => { pauseRecording(); setState("paused"); };
  const handleResume = () => { resumeRecording(); setState("recording"); };

  const handleStop = async () => {
    try {
      setState("processing");
      const audioBlob = await stopRecording();
      const formData = new FormData();
      formData.append("audio", audioBlob, `recording.${audioBlob.type.includes("webm") ? "webm" : "mp4"}`);
      if (selectedProject) formData.append("project_code", selectedProject);
      if (meetingTitle) formData.append("meeting_title", meetingTitle);
      if (attendees.length > 0) formData.append("attendees", JSON.stringify(attendees));
      const response = await fetch(`${API_BASE_URL}/api/recordings/upload`, { method: "POST", body: formData });
      if (!response.ok) throw new Error((await response.json()).detail || "Upload failed");
      setResult(await response.json());
      setState("complete");
    } catch (err) { setErrorMessage(err instanceof Error ? err.message : "Processing failed"); setState("error"); }
  };

  const handleReset = () => { setState("idle"); setStartTime(null); setResult(null); setErrorMessage(null); setMeetingTitle(""); setAttendees([]); };

  if (!isSupported) return (
    <Card className="border-red-200 bg-red-50"><CardContent className="py-12 text-center">
      <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" /><p className="text-lg font-medium text-red-700 mb-2">Recording Not Supported</p><p className="text-sm text-red-600">{recorderError}</p>
    </CardContent></Card>
  );

  return (
    <Card className="border-slate-200 overflow-hidden"><CardContent className="p-0">
      <div className={cn("relative p-8 text-center transition-all duration-500",
        state === "recording" && "bg-gradient-to-br from-red-50 to-red-100",
        state === "paused" && "bg-gradient-to-br from-amber-50 to-amber-100",
        state === "processing" && "bg-gradient-to-br from-blue-50 to-blue-100",
        state === "complete" && "bg-gradient-to-br from-emerald-50 to-emerald-100",
        state === "error" && "bg-gradient-to-br from-red-50 to-red-100",
        state === "idle" && "bg-gradient-to-br from-slate-50 to-slate-100"
      )}>
        {state === "recording" && <div className="absolute top-4 right-4 flex items-center gap-2"><span className="relative flex h-3 w-3"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span><span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span></span><span className="text-sm font-medium text-red-600">Recording</span></div>}
        {(state === "recording" || state === "paused") && <div className="mb-6"><RecordingTimer startTime={startTime} />{state === "paused" && <Badge className="mt-2 bg-amber-100 text-amber-700 border-0">Paused</Badge>}</div>}
        {state === "processing" && <div className="mb-6"><Loader2 className="mx-auto h-12 w-12 text-blue-500 animate-spin mb-4" /><p className="text-lg font-medium text-blue-700">Processing...</p><p className="text-sm text-blue-600 mt-1">Transcribing and extracting action items</p></div>}
        {state === "complete" && <div className="mb-6"><div className="mx-auto h-12 w-12 rounded-full bg-emerald-500 flex items-center justify-center mb-4"><Check className="h-6 w-6 text-white" /></div><p className="text-lg font-medium text-emerald-700">Recording Complete!</p></div>}
        {state === "error" && <div className="mb-6"><AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" /><p className="text-lg font-medium text-red-700">Processing Failed</p><p className="text-sm text-red-600 mt-1">{errorMessage}</p></div>}
        {state === "idle" && <div className="mb-6"><div className="mx-auto h-20 w-20 rounded-full bg-slate-200 flex items-center justify-center mb-4"><Mic className="h-10 w-10 text-slate-500" /></div><p className="text-lg font-medium text-slate-700">Ready to Record</p><p className="text-sm text-slate-500 mt-1">Select a project and click Start Recording</p></div>}
        <div className="flex justify-center gap-3">
          {state === "idle" && <Button size="lg" onClick={handleStart} className="gap-2 bg-red-500 hover:bg-red-600 text-white px-8"><Mic className="h-5 w-5" />Start Recording</Button>}
          {state === "recording" && <><Button size="lg" variant="outline" onClick={handlePause} className="gap-2"><Pause className="h-5 w-5" />Pause</Button><Button size="lg" onClick={handleStop} className="gap-2 bg-slate-900 hover:bg-slate-800"><Square className="h-5 w-5" />Stop & Process</Button></>}
          {state === "paused" && <><Button size="lg" variant="outline" onClick={handleResume} className="gap-2"><Play className="h-5 w-5" />Resume</Button><Button size="lg" onClick={handleStop} className="gap-2 bg-slate-900 hover:bg-slate-800"><Square className="h-5 w-5" />Stop & Process</Button></>}
          {(state === "complete" || state === "error") && <Button size="lg" onClick={handleReset} className="gap-2"><Mic className="h-5 w-5" />New Recording</Button>}
        </div>
      </div>
      {state === "idle" && (
        <div className="p-6 border-t border-slate-200 space-y-6">
          <div className="space-y-2"><Label className="flex items-center gap-2"><Briefcase className="h-4 w-4" />Project (Optional)</Label>
            <Select value={selectedProject} onValueChange={(v) => setSelectedProject(v === "_none" ? "" : v)}><SelectTrigger><SelectValue placeholder="Select a project..." /></SelectTrigger>
              <SelectContent><SelectItem value="_none">No project</SelectItem>{projects.map(p => <SelectItem key={p.project_code} value={p.project_code}><span className="font-mono text-xs mr-2">{p.project_code}</span>{p.project_name}</SelectItem>)}</SelectContent>
            </Select></div>
          <div className="space-y-2"><Label className="flex items-center gap-2"><Clock className="h-4 w-4" />Meeting Title (Optional)</Label><Input placeholder="e.g., Weekly Design Review" value={meetingTitle} onChange={e => setMeetingTitle(e.target.value)} /></div>
          <AttendeeInput attendees={attendees} onAdd={n => setAttendees([...attendees, n])} onRemove={i => setAttendees(attendees.filter((_, idx) => idx !== i))} />
        </div>
      )}
      {state === "complete" && result && <div className="p-6 border-t border-slate-200"><ResultsView result={result} /></div>}
    </CardContent></Card>
  );
}
