"use client";

/**
 * Login Page
 *
 * Simple email/password login form.
 */

import { useEffect, useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [localTime, setLocalTime] = useState("--");
  const [localDate, setLocalDate] = useState("--");
  const [timeZone, setTimeZone] = useState("--");
  const [weather, setWeather] = useState<{
    temperature: string;
    description: string;
    location: string;
  } | null>(null);
  const [weatherStatus, setWeatherStatus] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });

      if (result?.error) {
        setError("Invalid email or password");
      } else {
        router.push("/");
        router.refresh();
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (date: Date) =>
    new Intl.DateTimeFormat("en-US", {
      hour: "numeric",
      minute: "2-digit",
    }).format(date);

  const formatDate = (date: Date) =>
    new Intl.DateTimeFormat("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
    }).format(date);

  const weatherLabel = (code: number) => {
    if ([0].includes(code)) return "Clear";
    if ([1, 2].includes(code)) return "Mostly clear";
    if ([3].includes(code)) return "Overcast";
    if ([45, 48].includes(code)) return "Fog";
    if ([51, 53, 55].includes(code)) return "Drizzle";
    if ([61, 63, 65].includes(code)) return "Rain";
    if ([71, 73, 75].includes(code)) return "Snow";
    if ([80, 81, 82].includes(code)) return "Showers";
    if ([95, 96, 99].includes(code)) return "Storm";
    return "Conditions";
  };

  const fetchWeather = async () => {
    setWeatherStatus("loading");

    const fetchByCoords = async (
      lat: number,
      lon: number,
      locationLabel: string
    ) => {
      const url =
        "https://api.open-meteo.com/v1/forecast" +
        `?latitude=${lat}&longitude=${lon}` +
        "&current=temperature_2m,weather_code&temperature_unit=fahrenheit";
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error("Weather unavailable");
      }
      const data = await response.json();
      const temperature = data?.current?.temperature_2m;
      const code = data?.current?.weather_code;
      return {
        temperature:
          typeof temperature === "number" ? `${Math.round(temperature)}` : "--",
        description: weatherLabel(typeof code === "number" ? code : 0),
        location: locationLabel,
      };
    };

    try {
      if ("geolocation" in navigator) {
        const coords = await new Promise<GeolocationCoordinates>(
          (resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
              (position) => resolve(position.coords),
              (error) => reject(error),
              { timeout: 5000 }
            );
          }
        );
        const weatherData = await fetchByCoords(
          coords.latitude,
          coords.longitude,
          "Your area"
        );
        setWeather(weatherData);
        setWeatherStatus("ready");
        return;
      }
    } catch {
      // fall through to IP-based lookup
    }

    try {
      const locationResponse = await fetch("https://ipapi.co/json/");
      if (!locationResponse.ok) {
        throw new Error("Location unavailable");
      }
      const locationData = await locationResponse.json();
      const weatherData = await fetchByCoords(
        locationData.latitude,
        locationData.longitude,
        `${locationData.city || "Local area"}${
          locationData.region ? `, ${locationData.region}` : ""
        }`
      );
      setWeather(weatherData);
      setWeatherStatus("ready");
    } catch {
      setWeatherStatus("error");
    }
  };

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setLocalTime(formatTime(now));
      setLocalDate(formatDate(now));
      setTimeZone(Intl.DateTimeFormat().resolvedOptions().timeZone || "--");
    };
    updateTime();
    const timer = setInterval(updateTime, 60 * 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetchWeather();
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#eef2f7] text-slate-900">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(15,23,42,0.12),_transparent_55%)]"
        aria-hidden="true"
      />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(15,23,42,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(15,23,42,0.06)_1px,transparent_1px)] bg-[size:90px_90px]" />

      <div className="relative mx-auto grid min-h-screen max-w-6xl gap-12 px-6 py-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <section className="space-y-6">
          <div className="flex items-center gap-3 text-[11px] uppercase tracking-[0.35em] text-slate-500">
            <span className="h-2 w-2 rounded-full bg-emerald-500/70" />
            Bensley Design Studios
          </div>
          <h1 className="text-3xl font-semibold text-slate-900 sm:text-4xl">
            Welcome back.
          </h1>
          <p className="max-w-lg text-sm text-slate-600">
            Sign in to continue. Your briefing loads immediately after authentication.
          </p>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-200/70 bg-white/85 p-4 shadow-sm backdrop-blur">
              <p className="text-[11px] uppercase tracking-[0.28em] text-slate-500">
                Local time
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">
                {localTime}
              </p>
              <p className="text-xs text-slate-500">{localDate}</p>
              <p className="text-[11px] text-slate-400">{timeZone}</p>
            </div>
            <div className="rounded-2xl border border-slate-200/70 bg-white/85 p-4 shadow-sm backdrop-blur">
              <p className="text-[11px] uppercase tracking-[0.28em] text-slate-500">
                Local conditions
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">
                {weather?.temperature ?? "--"}°
              </p>
              <p className="text-xs text-slate-500">
                {weatherStatus === "loading"
                  ? "Fetching weather..."
                  : weatherStatus === "error"
                  ? "Weather unavailable"
                  : weather?.description ?? "Conditions"}
              </p>
              <p className="text-xs text-slate-400">
                {weather?.location ?? "Based on your location"}
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200/70 bg-white/85 p-4 text-sm text-slate-600 shadow-sm">
            <p className="text-[11px] uppercase tracking-[0.28em] text-slate-500">
              Studio note
            </p>
            <p className="mt-2 text-sm text-slate-700">
              Proposals, project health, and finance summaries load after sign in.
            </p>
          </div>
        </section>

        <Card className="w-full max-w-md justify-self-center border-slate-200/70 bg-white/90 shadow-xl backdrop-blur">
          <CardHeader className="space-y-2">
            <CardTitle className="text-2xl font-semibold text-slate-900">
              Studio access
            </CardTitle>
            <CardDescription>
              Use your Bensley credentials to continue.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@bensley.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="bg-slate-50/80"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="bg-slate-50/80"
                />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button
                type="submit"
                className="w-full bg-slate-900 text-white hover:bg-slate-800"
                disabled={loading}
              >
                {loading ? "Signing in..." : "Sign in"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
