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

type WeatherState = {
  temperature: string;
  description: string;
  location: string;
  humidity: string;
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [greeting, setGreeting] = useState("Welcome");
  const [localTime, setLocalTime] = useState("--");
  const [localDate, setLocalDate] = useState("--");
  const [timeZone, setTimeZone] = useState("--");
  const [weather, setWeather] = useState<WeatherState | null>(null);
  const [weatherStatus, setWeatherStatus] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle");
  const [headlines, setHeadlines] = useState<
    Array<{ title: string; url: string; source: string }>
  >([]);
  const [headlinesStatus, setHeadlinesStatus] = useState<
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
    if (code === 0) return "Clear";
    if ([1, 2].includes(code)) return "Mostly clear";
    if (code === 3) return "Overcast";
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
        "&current=temperature_2m,relative_humidity_2m,weather_code&temperature_unit=celsius";
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error("Weather unavailable");
      }
      const data = await response.json();
      const temperature = data?.current?.temperature_2m;
      const humidity = data?.current?.relative_humidity_2m;
      const code = data?.current?.weather_code;
      return {
        temperature:
          typeof temperature === "number" ? `${Math.round(temperature)}` : "--",
        description: weatherLabel(typeof code === "number" ? code : 0),
        location: locationLabel,
        humidity:
          typeof humidity === "number" ? `${Math.round(humidity)}` : "--",
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
      const hour = now.getHours();
      if (hour >= 5 && hour < 12) {
        setGreeting("Good morning");
      } else if (hour >= 12 && hour < 17) {
        setGreeting("Good afternoon");
      } else if (hour >= 17 && hour < 22) {
        setGreeting("Good evening");
      } else {
        setGreeting("Welcome back");
      }
    };
    updateTime();
    const timer = setInterval(updateTime, 60 * 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetchWeather();
  }, []);

  useEffect(() => {
    const fetchHeadlines = async () => {
      setHeadlinesStatus("loading");
      const endpoint = process.env.NEXT_PUBLIC_NEWS_ENDPOINT;
      const feedEnv = process.env.NEXT_PUBLIC_NEWS_FEEDS;
      const feedUrls = feedEnv
        ? feedEnv.split(",").map((item) => item.trim()).filter(Boolean)
        : [];
      const defaultFeeds = [
        "https://www.dezeen.com/feed/",
        "https://www.archdaily.com/rss",
        "https://www.designboom.com/feed/",
      ];
      const feeds = feedUrls.length > 0 ? feedUrls : defaultFeeds;

      try {
        if (endpoint) {
          const response = await fetch(endpoint);
          if (!response.ok) {
            throw new Error("News unavailable");
          }
          const data = await response.json();
          const items = (data?.results ?? data?.articles ?? data?.items ?? []).slice(
            0,
            4
          );
          const mapped = items.map((item: any) => ({
            title: item.title ?? "Untitled",
            url: item.url ?? item.link ?? "#",
            source: item.news_site ?? item.source ?? item.author ?? "External",
          }));
          setHeadlines(mapped);
          setHeadlinesStatus("ready");
          return;
        }

        const fetchFeed = async (feedUrl: string) => {
          const requestUrl = feedUrl.includes("rss2json")
            ? feedUrl
            : `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(
                feedUrl
              )}`;
          const response = await fetch(requestUrl);
          if (!response.ok) {
            throw new Error("Feed unavailable");
          }
          const data = await response.json();
          return (data?.items ?? []).map((item: any) => ({
            title: item.title ?? "Untitled",
            url: item.link ?? "#",
            source: data?.feed?.title ?? "External",
          }));
        };

        const results = await Promise.allSettled(
          feeds.map((feed) => fetchFeed(feed))
        );
        const flattened = results
          .filter((result): result is PromiseFulfilledResult<any[]> => result.status === "fulfilled")
          .flatMap((result) => result.value);
        const unique = Array.from(
          new Map(flattened.map((item) => [item.url, item])).values()
        ).slice(0, 4);

        setHeadlines(unique);
        setHeadlinesStatus("ready");
      } catch {
        setHeadlinesStatus("error");
      }
    };

    fetchHeadlines();
  }, []);

  return (
    <div className="relative min-h-screen w-screen overflow-hidden bg-slate-50 text-slate-900">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-slate-900/70 via-blue-700/40 to-transparent" />
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(30,58,138,0.08),_transparent_70%)]"
        aria-hidden="true"
      />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_85%_30%,_rgba(15,23,42,0.03),_transparent_55%)]" />
      <div className="pointer-events-none absolute -right-24 top-10 h-72 w-72 rounded-full bg-blue-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -left-16 bottom-10 h-64 w-64 rounded-full bg-amber-400/12 blur-3xl" />

      <div className="relative mx-auto grid min-h-screen max-w-6xl gap-12 px-6 py-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <section className="space-y-6">
          <div className="flex items-center gap-3 text-[11px] uppercase tracking-[0.35em] text-slate-500">
            <span className="h-2 w-2 rounded-full bg-slate-900/80" />
            Bensley Design Studios
          </div>
          <h1 className="text-3xl font-semibold text-slate-900 sm:text-4xl">
            {greeting}.
          </h1>
          <p className="max-w-lg text-sm text-slate-600">
            Sign in to open the studio workspace. Your briefing loads immediately after authentication.
          </p>
          <div className="h-px w-32 bg-gradient-to-r from-slate-900/80 via-blue-500/60 to-transparent" />

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-4 shadow-sm backdrop-blur">
              <p className="text-[11px] uppercase tracking-[0.28em] text-slate-500">
                Local time
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">
                {localTime}
              </p>
              <p className="text-xs text-slate-500">{localDate}</p>
              <p className="text-[11px] text-slate-400">{timeZone}</p>
            </div>
            <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-4 shadow-sm backdrop-blur">
              <p className="text-[11px] uppercase tracking-[0.28em] text-slate-500">
                Local conditions
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">
                {weather?.temperature ?? "--"}°C
              </p>
              <p className="text-xs text-slate-500">
                {weatherStatus === "loading"
                  ? "Fetching weather..."
                  : weatherStatus === "error"
                  ? "Weather unavailable"
                  : weather?.description ?? "Conditions"}
              </p>
              <p className="text-xs text-slate-400">
                {weather?.humidity ?? "--"}% humidity
              </p>
              <p className="text-xs text-slate-400">
                {weather?.location ?? "Based on your location"}
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200/70 bg-white/90 p-4 text-sm text-slate-600 shadow-sm">
            <p className="text-[11px] uppercase tracking-[0.28em] text-slate-500">
              Design & hospitality headlines
            </p>
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              {headlinesStatus === "loading" && (
                <p className="text-sm text-slate-500">Loading headlines...</p>
              )}
              {headlinesStatus === "error" && (
                <p className="text-sm text-slate-500">
                  Headlines unavailable.
                </p>
              )}
              {headlinesStatus === "ready" &&
                headlines.map((item) => (
                  <a
                    key={`${item.title}-${item.source}`}
                    className="flex items-start gap-2 text-sm text-slate-700 hover:text-slate-900"
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <span className="mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-blue-600/70" />
                    <span>
                      {item.title}
                      <span className="ml-2 text-xs text-slate-400">
                        {item.source}
                      </span>
                    </span>
                  </a>
                ))}
            </div>
            <p className="mt-3 text-xs text-slate-500">
              Bangkok studio • UTC+7
            </p>
          </div>
        </section>

        <Card className="w-full max-w-md justify-self-center border-slate-200/70 bg-white/95 text-slate-900 shadow-xl backdrop-blur">
          <CardHeader className="space-y-2">
            <CardTitle className="text-2xl font-semibold text-slate-900">
              Studio access
            </CardTitle>
            <CardDescription className="text-slate-500">
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
                  className="bg-white"
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
                  className="bg-white"
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
