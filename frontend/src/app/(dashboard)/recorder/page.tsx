"use client";

import { MeetingRecorder } from "@/components/recorder/meeting-recorder";
import { Card, CardContent } from "@/components/ui/card";
import { Mic, FileText, CheckSquare, Zap } from "lucide-react";

function PageHeader() {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-teal-900 via-teal-800 to-slate-900 p-8 text-white">
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-full h-full" style={{ backgroundImage: `radial-gradient(circle at 25% 25%, rgba(255,255,255,0.2) 1px, transparent 1px)`, backgroundSize: "32px 32px" }} />
      </div>
      <div className="relative">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 rounded-xl bg-white/10 backdrop-blur"><Mic className="h-6 w-6" /></div>
          <h1 className="text-3xl font-bold tracking-tight">Meeting Recorder</h1>
        </div>
        <p className="text-teal-200 max-w-xl">Record meetings from your browser. Audio is automatically transcribed, summarized, and action items are extracted as tasks.</p>
      </div>
    </div>
  );
}

function FeatureCards() {
  const features = [
    { icon: Mic, title: "Browser Recording", description: "Record directly from any device with a microphone", color: "text-teal-600", bg: "bg-teal-50" },
    { icon: FileText, title: "Auto Transcription", description: "Whisper AI converts speech to text automatically", color: "text-blue-600", bg: "bg-blue-50" },
    { icon: Zap, title: "Smart Summary", description: "AI generates key points and meeting summary", color: "text-amber-600", bg: "bg-amber-50" },
    { icon: CheckSquare, title: "Action Items", description: "Tasks are extracted and added to your task list", color: "text-emerald-600", bg: "bg-emerald-50" },
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {features.map((f) => (
        <Card key={f.title} className="border-slate-200"><CardContent className="p-4">
          <div className={`p-2 rounded-lg ${f.bg} ${f.color} w-fit mb-3`}><f.icon className="h-4 w-4" /></div>
          <h3 className="font-semibold text-slate-900 text-sm">{f.title}</h3>
          <p className="text-xs text-slate-500 mt-1">{f.description}</p>
        </CardContent></Card>
      ))}
    </div>
  );
}

export default function RecorderPage() {
  return (
    <div className="space-y-6 w-full max-w-4xl mx-auto">
      <PageHeader />
      <FeatureCards />
      <MeetingRecorder />
    </div>
  );
}
