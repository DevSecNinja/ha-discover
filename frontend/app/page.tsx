"use client";

import { useEffect, useState } from "react";

interface Repository {
  name: string;
  owner: string;
  description: string | null;
  url: string;
  stars: number;
}

interface Automation {
  id: number;
  alias: string | null;
  description: string | null;
  trigger_types: string[];
  blueprint_path: string | null;
  action_calls: string[];
  source_file_path: string;
  github_url: string;
  start_line: number | null;
  end_line: number | null;
  repository: Repository;
  indexed_at: string | null;
}

interface RepositoryFacet {
  owner: string;
  name: string;
  stars: number;
  count: number;
}

interface BlueprintFacet {
  path: string;
  count: number;
}

interface TriggerFacet {
  type: string;
  count: number;
}

interface ActionFacet {
  call: string;
  count: number;
}

interface Facets {
  repositories: RepositoryFacet[];
  blueprints: BlueprintFacet[];
  triggers: TriggerFacet[];
  actions: ActionFacet[];
}

interface SearchResponse {
  query: string;
  results: Automation[];
  count: number;
  facets: Facets;
}

interface Statistics {
  total_repositories: number;
  total_automations: number;
  last_indexed_at: string | null;
  repo_star_count: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
const IS_DEVELOPMENT = process.env.NODE_ENV === "development";

if (!API_BASE_URL) {
  console.error("NEXT_PUBLIC_API_URL environment variable is not set");
}

if (IS_DEVELOPMENT) {
  console.info("🚧 Running in development mode");
}

// Helper function to construct GitHub URL with line numbers
function getGitHubUrlWithLines(automation: Automation): string {
  const { github_url, start_line, end_line } = automation;
  if (start_line && end_line) {
    return `${github_url}#L${start_line}-L${end_line}`;
  }
  if (start_line) {
    return `${github_url}#L${start_line}`;
  }
  return github_url;
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Automation[]>([]);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [indexing, setIndexing] = useState(false);
  const [isDark, setIsDark] = useState(true);
  const [facets, setFacets] = useState<Facets>({
    repositories: [],
    blueprints: [],
    triggers: [],
    actions: [],
  });
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);
  const [selectedBlueprint, setSelectedBlueprint] = useState<string | null>(
    null,
  );
  const [selectedTrigger, setSelectedTrigger] = useState<string | null>(null);
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // Load theme preference from localStorage
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
      setIsDark(savedTheme === "dark");
    } else {
      // Check system preference
      const prefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)",
      ).matches;
      setIsDark(prefersDark);
    }

    // Check if mobile viewport and set initial state
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
    };

    // Set initial mobile state
    const initialMobile = window.innerWidth < 768;
    setIsMobile(initialMobile);
    // Hide filters by default on mobile on initial load
    if (initialMobile) {
      setShowFilters(false);
    }

    // Debounced resize handler to update isMobile state
    let resizeTimeout: number | undefined;

    const handleResize = () => {
      if (resizeTimeout !== undefined) {
        window.clearTimeout(resizeTimeout);
      }
      resizeTimeout = window.setTimeout(() => {
        checkMobile();
      }, 200);
    };

    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      if (resizeTimeout !== undefined) {
        window.clearTimeout(resizeTimeout);
      }
    };
  }, []);

  const fetchStatistics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/statistics`);
      const data = await response.json();
      setStatistics(data);
    } catch (error) {
      console.error("Error fetching statistics:", error);
    }
  };

  const performSearch = async (searchQuery: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("q", searchQuery);
      if (selectedRepo) params.append("repo", selectedRepo);
      if (selectedBlueprint) params.append("blueprint", selectedBlueprint);
      if (selectedTrigger) params.append("trigger", selectedTrigger);
      if (selectedAction) params.append("action", selectedAction);

      const response = await fetch(
        `${API_BASE_URL}/search?${params.toString()}`,
      );
      const data: SearchResponse = await response.json();
      setResults(data.results);
      setFacets(data.facets);
    } catch (error) {
      console.error("Error searching:", error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // biome-ignore lint/correctness/useExhaustiveDependencies: Functions are stable and should only run on mount
  useEffect(() => {
    // Load statistics on mount
    fetchStatistics();
    // Load initial results
    performSearch("");
  }, []);

  // Re-run search when filters change
  // biome-ignore lint/correctness/useExhaustiveDependencies: Filter changes should trigger search
  useEffect(() => {
    performSearch(query);
  }, [selectedRepo, selectedBlueprint, selectedTrigger, selectedAction]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query);
  };

  const handleTriggerIndexing = async () => {
    setIndexing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/index`, {
        method: "POST",
      });

      if (response.status === 429) {
        const data = await response.json();
        alert(`Rate limit exceeded: ${data.detail}`);
      } else if (response.ok) {
        const data = await response.json();
        if (data.started) {
          alert(
            "Indexing started! This may take a few minutes. Refresh the page to see updated results.",
          );
        }
      } else {
        alert("Failed to trigger indexing");
      }
    } catch (error) {
      console.error("Error triggering indexing:", error);
      alert("Failed to trigger indexing");
    } finally {
      setIndexing(false);
    }
  };

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    localStorage.setItem("theme", newTheme ? "dark" : "light");
  };

  const formatLastIndexed = (isoString: string | null) => {
    if (!isoString) return null;

    try {
      const date = new Date(isoString);
      // Format in user's local timezone
      return date.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZoneName: "short",
      });
    } catch (error) {
      console.error("Error formatting date:", error);
      return null;
    }
  };

  return (
    <div
      className="min-h-screen relative overflow-hidden"
      style={{
        backgroundColor: isDark ? "transparent" : "#ffffff",
      }}
    >
      {/* Theme Toggle Button */}
      <button
        type="button"
        onClick={toggleTheme}
        className="fixed top-6 right-6 z-50 p-3 rounded-full backdrop-blur-xl transition-all duration-300 hover:scale-105"
        style={{
          background: isDark
            ? "rgba(20, 20, 35, 0.85)"
            : "rgba(255, 255, 255, 0.9)",
          border: isDark
            ? "1px solid rgba(255, 255, 255, 0.1)"
            : "1px solid rgba(0, 0, 0, 0.06)",
          boxShadow: isDark
            ? "0 2px 12px rgba(0, 0, 0, 0.4)"
            : "0 2px 8px rgba(0, 0, 0, 0.08)",
        }}
        title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      >
        {isDark ? (
          <svg
            className="w-5 h-5"
            style={{ color: "#a78bfa" }}
            fill="currentColor"
            viewBox="0 0 24 24"
            role="img"
            aria-label="Switch to light mode"
          >
            <path
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          </svg>
        ) : (
          <svg
            className="w-5 h-5 text-indigo-600"
            fill="currentColor"
            viewBox="0 0 24 24"
            role="img"
            aria-label="Switch to dark mode"
          >
            <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
          </svg>
        )}
      </button>

      {/* Animated Background */}
      <div
        className={`fixed inset-0 -z-10 ${isDark ? "gradient-bg" : "gradient-bg-light"}`}
      ></div>
      {isDark && (
        <>
          <div
            className="fixed inset-0 -z-10"
            style={{
              background:
                "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(109, 40, 217, 0.15), transparent)",
            }}
          ></div>
          <div
            className="fixed inset-0 -z-10"
            style={{
              background:
                "radial-gradient(ellipse 60% 50% at 80% 60%, rgba(18, 188, 242, 0.08), transparent)",
            }}
          ></div>
        </>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <header className="text-center mb-16 pt-8">
          <div
            className="inline-flex items-center gap-2.5 mb-8 px-4 py-2 rounded-full backdrop-blur-xl"
            style={{
              background: isDark
                ? "rgba(25, 25, 40, 0.6)"
                : "rgba(255, 255, 255, 0.7)",
              border: isDark
                ? "1px solid rgba(255, 255, 255, 0.08)"
                : "1px solid rgba(0, 0, 0, 0.08)",
            }}
          >
            <svg
              className="w-4 h-4"
              style={{ color: "#12bcf2" }}
              fill="currentColor"
              viewBox="0 0 24 24"
              role="img"
              aria-label="hadiscover logo"
            >
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" />
            </svg>
            <span
              className="text-sm font-medium"
              style={{
                color: isDark
                  ? "rgba(255, 255, 255, 0.7)"
                  : "rgba(0, 0, 0, 0.7)",
                opacity: 0.9,
              }}
            >
              Home Assistant Automation Discovery
            </span>
          </div>

          <h1 className="text-7xl sm:text-8xl font-bold mb-6 tracking-tight">
            <span
              className="bg-clip-text text-transparent"
              style={{
                backgroundImage: isDark
                  ? "linear-gradient(to right, #ffffff, #e0e7ff, #c7d2fe)"
                  : "linear-gradient(to right, #1f2937, #4338ca, #6d28d9)",
                WebkitBackgroundClip: "text",
                backgroundClip: "text",
              }}
            >
              hadiscover
            </span>
          </h1>

          <p
            className="text-2xl sm:text-3xl mb-4 font-light max-w-3xl mx-auto leading-relaxed"
            style={{
              color: isDark ? "rgba(255, 255, 255, 0.6)" : "rgba(0, 0, 0, 0.7)",
            }}
          >
            Discover Home Assistant automations from the community
          </p>

          {statistics && (
            <div className="flex items-center justify-center gap-6 mt-10">
              <div
                className="rounded-2xl px-8 py-5 backdrop-blur-xl"
                style={{
                  background: isDark
                    ? "rgba(25, 25, 40, 0.6)"
                    : "rgba(255, 255, 255, 0.8)",
                  border: isDark
                    ? "1px solid rgba(255, 255, 255, 0.08)"
                    : "1px solid rgba(0, 0, 0, 0.08)",
                  boxShadow: isDark
                    ? "0 4px 16px rgba(0, 0, 0, 0.25)"
                    : "0 2px 8px rgba(0, 0, 0, 0.05)",
                }}
              >
                <div
                  className="text-3xl font-bold mb-1"
                  style={{
                    color: isDark ? "#e0e7ff" : "#1f2937",
                  }}
                >
                  {statistics.total_automations.toLocaleString()}
                </div>
                <div
                  className="text-sm"
                  style={{
                    color: isDark
                      ? "rgba(255, 255, 255, 0.5)"
                      : "rgba(0, 0, 0, 0.5)",
                  }}
                >
                  Automations
                </div>
              </div>
              <div
                className="rounded-2xl px-8 py-5 backdrop-blur-xl"
                style={{
                  background: isDark
                    ? "rgba(25, 25, 40, 0.6)"
                    : "rgba(255, 255, 255, 0.8)",
                  border: isDark
                    ? "1px solid rgba(255, 255, 255, 0.08)"
                    : "1px solid rgba(0, 0, 0, 0.08)",
                  boxShadow: isDark
                    ? "0 4px 16px rgba(0, 0, 0, 0.25)"
                    : "0 2px 8px rgba(0, 0, 0, 0.05)",
                }}
              >
                <div
                  className="text-3xl font-bold mb-1"
                  style={{
                    color: isDark ? "#e0e7ff" : "#1f2937",
                  }}
                >
                  {statistics.total_repositories.toLocaleString()}
                </div>
                <div
                  className="text-sm"
                  style={{
                    color: isDark
                      ? "rgba(255, 255, 255, 0.5)"
                      : "rgba(0, 0, 0, 0.5)",
                  }}
                >
                  Repositories
                </div>
              </div>
            </div>
          )}
        </header>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="mb-16">
          <div className="flex flex-col sm:flex-row gap-3 max-w-4xl mx-auto">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                <svg
                  className="w-5 h-5"
                  style={{
                    color: isDark
                      ? "rgba(255, 255, 255, 0.4)"
                      : "rgba(0, 0, 0, 0.4)",
                  }}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  role="img"
                  aria-label="Search icon"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search automations, triggers, actions..."
                className="w-full pl-12 pr-12 py-5 text-lg rounded-2xl border focus:outline-none focus:ring-1 focus:border-transparent transition-all duration-200"
                style={{
                  color: isDark ? "#e0e7ff" : "#1f2937",
                  background: isDark
                    ? "rgba(25, 25, 40, 0.75)"
                    : "rgba(255, 255, 255, 0.9)",
                  backdropFilter: "blur(24px)",
                  borderColor: isDark
                    ? "rgba(255, 255, 255, 0.1)"
                    : "rgba(0, 0, 0, 0.1)",
                  boxShadow: isDark
                    ? "0 4px 16px rgba(0, 0, 0, 0.25)"
                    : "0 2px 8px rgba(0, 0, 0, 0.05)",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "#12bcf2";
                  e.currentTarget.style.boxShadow = isDark
                    ? "0 0 0 3px rgba(18, 188, 242, 0.1), 0 4px 16px rgba(0, 0, 0, 0.3)"
                    : "0 0 0 3px rgba(18, 188, 242, 0.1), 0 2px 8px rgba(0, 0, 0, 0.08)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = isDark
                    ? "rgba(255, 255, 255, 0.1)"
                    : "rgba(0, 0, 0, 0.1)";
                  e.currentTarget.style.boxShadow = isDark
                    ? "0 4px 16px rgba(0, 0, 0, 0.25)"
                    : "0 2px 8px rgba(0, 0, 0, 0.05)";
                }}
              />
              {query && (
                <button
                  type="button"
                  onClick={() => {
                    setQuery("");
                    performSearch("");
                  }}
                  className="absolute inset-y-0 right-4 flex items-center hover:opacity-70 transition-opacity duration-200"
                  aria-label="Clear search"
                  title="Clear search"
                >
                  <svg
                    className="w-5 h-5"
                    style={{
                      color: isDark
                        ? "rgba(255, 255, 255, 0.5)"
                        : "rgba(0, 0, 0, 0.5)",
                    }}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              )}
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-8 py-5 text-white font-semibold rounded-2xl focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              style={{
                background: isDark
                  ? "linear-gradient(135deg, rgba(109, 40, 217, 0.8), rgba(147, 51, 234, 0.8))"
                  : "linear-gradient(135deg, rgb(109, 40, 217), rgb(147, 51, 234))",
                border: isDark ? "1px solid rgba(147, 51, 234, 0.3)" : "none",
                boxShadow: isDark
                  ? "0 4px 12px rgba(109, 40, 217, 0.25)"
                  : "0 4px 12px rgba(109, 40, 217, 0.3)",
                backdropFilter: isDark ? "blur(12px)" : "none",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = isDark
                  ? "0 6px 16px rgba(109, 40, 217, 0.35)"
                  : "0 6px 16px rgba(109, 40, 217, 0.4)";
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = isDark
                  ? "0 4px 12px rgba(109, 40, 217, 0.25)"
                  : "0 4px 12px rgba(109, 40, 217, 0.3)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg
                    className="animate-spin h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Loading spinner"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Searching
                </span>
              ) : (
                "Search"
              )}
            </button>
          </div>
        </form>

        {/* Indexing Button - Only in development */}
        {IS_DEVELOPMENT && (
          <div className="text-center mb-12">
            <button
              type="button"
              onClick={handleTriggerIndexing}
              disabled={indexing}
              className="px-6 py-3 text-white font-medium rounded-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              style={{
                background: isDark
                  ? "linear-gradient(135deg, rgba(34, 197, 94, 0.8), rgba(16, 185, 129, 0.8))"
                  : "linear-gradient(135deg, rgb(34, 197, 94), rgb(16, 185, 129))",
                border: isDark ? "1px solid rgba(34, 197, 94, 0.3)" : "none",
                boxShadow: isDark
                  ? "0 4px 12px rgba(34, 197, 94, 0.2)"
                  : "0 4px 12px rgba(34, 197, 94, 0.25)",
                backdropFilter: isDark ? "blur(12px)" : "none",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = isDark
                  ? "0 6px 16px rgba(34, 197, 94, 0.3)"
                  : "0 6px 16px rgba(34, 197, 94, 0.35)";
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = isDark
                  ? "0 4px 12px rgba(34, 197, 94, 0.2)"
                  : "0 4px 12px rgba(34, 197, 94, 0.25)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              {indexing ? "Starting Indexing..." : "🔄 Trigger Re-Index"}
            </button>
            <p
              className="text-sm mt-3"
              style={{
                color: isDark
                  ? "rgba(255, 255, 255, 0.6)"
                  : "rgba(0, 0, 0, 0.5)",
              }}
            >
              Discover repositories with the{" "}
              <code
                className="px-2 py-1 rounded-lg text-[rgb(var(--ha-blue))] font-mono text-xs"
                style={{
                  background: isDark
                    ? "rgba(255, 255, 255, 0.1)"
                    : "rgba(0, 0, 0, 0.05)",
                }}
              >
                hadiscover
              </code>{" "}
              topic
            </p>
          </div>
        )}

        {/* Filters and Results */}
        <div className={`flex gap-6 relative ${isMobile ? "flex-col" : ""}`}>
          {/* Filter Section */}
          {(facets.repositories.length > 0 ||
            facets.blueprints.length > 0 ||
            facets.triggers.length > 0 ||
            facets.actions.length > 0) && (
            <>
              <aside
                className={`
                  ${isMobile ? "w-full" : showFilters ? "w-80 flex-shrink-0" : "w-12 flex-shrink-0"}
                  transition-all duration-300
                `}
              >
                {/* Toggle Button */}
                <button
                  type="button"
                  onClick={() => setShowFilters(!showFilters)}
                  className={`
                    mb-4 p-3 rounded-2xl backdrop-blur-xl transition-all duration-200 hover:scale-105
                    ${isMobile ? "w-full" : "w-full"}
                  `}
                  style={{
                    background: isDark
                      ? "rgba(25, 25, 40, 0.6)"
                      : "rgba(255, 255, 255, 0.8)",
                    border: isDark
                      ? "1px solid rgba(255, 255, 255, 0.08)"
                      : "1px solid rgba(0, 0, 0, 0.08)",
                  }}
                >
                  <div className="flex items-center justify-center gap-2">
                    <svg
                      className="w-5 h-5"
                      style={{
                        color: isDark ? "#a78bfa" : "#7c3aed",
                        transform: showFilters
                          ? "rotate(0deg)"
                          : "rotate(180deg)",
                        transition: "transform 0.3s",
                      }}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      role="img"
                      aria-label={showFilters ? "Hide filters" : "Show filters"}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                      />
                    </svg>
                    {(isMobile || showFilters) && (
                      <span
                        className="font-semibold"
                        style={{
                          color: isDark ? "#e0e7ff" : "#1f2937",
                        }}
                      >
                        Filters
                      </span>
                    )}
                  </div>
                </button>

                {showFilters && (
                  <div
                    className={`
                      rounded-3xl backdrop-blur-xl p-6
                      ${isMobile ? "space-y-4" : "space-y-6 sticky top-6"}
                    `}
                    style={{
                      background: isDark
                        ? "rgba(25, 25, 40, 0.6)"
                        : "rgba(255, 255, 255, 0.8)",
                      border: isDark
                        ? "1px solid rgba(255, 255, 255, 0.08)"
                        : "1px solid rgba(0, 0, 0, 0.08)",
                    }}
                  >
                    {/* Active Filters */}
                    {(selectedRepo ||
                      selectedBlueprint ||
                      selectedTrigger ||
                      selectedAction) && (
                      <div
                        className="pb-4 border-b"
                        style={{
                          borderColor: isDark
                            ? "rgba(255, 255, 255, 0.1)"
                            : "rgba(0, 0, 0, 0.1)",
                        }}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <h3
                            className="text-sm font-semibold"
                            style={{
                              color: isDark ? "#e0e7ff" : "#1f2937",
                            }}
                          >
                            Active Filters
                          </h3>
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedRepo(null);
                              setSelectedBlueprint(null);
                              setSelectedTrigger(null);
                              setSelectedAction(null);
                            }}
                            className="text-xs px-2 py-1 rounded-lg transition-colors"
                            style={{
                              color: isDark ? "#f87171" : "#dc2626",
                              background: isDark
                                ? "rgba(248, 113, 113, 0.1)"
                                : "rgba(220, 38, 38, 0.1)",
                            }}
                          >
                            Clear All
                          </button>
                        </div>
                        <div className="space-y-2">
                          {selectedRepo && (
                            <div
                              className="flex items-center justify-between text-sm px-3 py-2 rounded-lg"
                              style={{
                                background: isDark
                                  ? "rgba(167, 139, 250, 0.15)"
                                  : "rgba(124, 58, 237, 0.1)",
                                color: isDark ? "#c4b5fd" : "#7c3aed",
                              }}
                            >
                              <span className="truncate">{selectedRepo}</span>
                              <button
                                type="button"
                                onClick={() => setSelectedRepo(null)}
                                className="ml-2 hover:opacity-70"
                              >
                                ✕
                              </button>
                            </div>
                          )}
                          {selectedBlueprint && (
                            <div
                              className="flex items-center justify-between text-sm px-3 py-2 rounded-lg"
                              style={{
                                background: isDark
                                  ? "rgba(96, 165, 250, 0.15)"
                                  : "rgba(37, 99, 235, 0.1)",
                                color: isDark ? "#93c5fd" : "#2563eb",
                              }}
                            >
                              <span className="truncate">
                                {selectedBlueprint.split("/").pop()}
                              </span>
                              <button
                                type="button"
                                onClick={() => setSelectedBlueprint(null)}
                                className="ml-2 hover:opacity-70"
                              >
                                ✕
                              </button>
                            </div>
                          )}
                          {selectedTrigger && (
                            <div
                              className="flex items-center justify-between text-sm px-3 py-2 rounded-lg"
                              style={{
                                background: isDark
                                  ? "rgba(52, 211, 153, 0.15)"
                                  : "rgba(16, 185, 129, 0.1)",
                                color: isDark ? "#6ee7b7" : "#10b981",
                              }}
                            >
                              <span className="truncate">
                                {selectedTrigger}
                              </span>
                              <button
                                type="button"
                                onClick={() => setSelectedTrigger(null)}
                                className="ml-2 hover:opacity-70"
                              >
                                ✕
                              </button>
                            </div>
                          )}
                          {selectedAction && (
                            <div
                              className="flex items-center justify-between text-sm px-3 py-2 rounded-lg"
                              style={{
                                background: isDark
                                  ? "rgba(251, 191, 36, 0.15)"
                                  : "rgba(245, 158, 11, 0.1)",
                                color: isDark ? "#fbbf24" : "#d97706",
                              }}
                            >
                              <span className="truncate font-mono text-xs">
                                {selectedAction}
                              </span>
                              <button
                                type="button"
                                onClick={() => setSelectedAction(null)}
                                className="ml-2 hover:opacity-70"
                              >
                                ✕
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Repository Filter */}
                    {facets.repositories.length > 0 && (
                      <div>
                        <h3
                          className="text-sm font-semibold mb-3"
                          style={{
                            color: isDark ? "#e0e7ff" : "#1f2937",
                          }}
                        >
                          📦 Repositories
                        </h3>
                        <div
                          className="space-y-2 pb-1"
                        >
                          {facets.repositories.map((repo) => {
                            const repoKey = `${repo.owner}/${repo.name}`;
                            const isSelected = selectedRepo === repoKey;
                            return (
                              <button
                                key={repoKey}
                                type="button"
                                onClick={() =>
                                  setSelectedRepo(isSelected ? null : repoKey)
                                }
                                className="w-full text-left px-3 py-2 rounded-lg transition-all duration-150"
                                style={{
                                  background: isSelected
                                    ? isDark
                                      ? "rgba(167, 139, 250, 0.2)"
                                      : "rgba(124, 58, 237, 0.15)"
                                    : isDark
                                      ? "rgba(255, 255, 255, 0.05)"
                                      : "rgba(0, 0, 0, 0.03)",
                                  border: isSelected
                                    ? isDark
                                      ? "1px solid rgba(167, 139, 250, 0.4)"
                                      : "1px solid rgba(124, 58, 237, 0.3)"
                                    : isDark
                                      ? "1px solid rgba(255, 255, 255, 0.05)"
                                      : "1px solid rgba(0, 0, 0, 0.05)",
                                }}
                                onMouseEnter={(e) => {
                                  if (isDark) {
                                    e.currentTarget.style.background =
                                      isSelected
                                        ? "rgba(167, 139, 250, 0.3)"
                                        : "rgba(255, 255, 255, 0.1)";
                                    e.currentTarget.style.boxShadow =
                                      "0 4px 12px rgba(0, 0, 0, 0.2)";
                                  } else {
                                    e.currentTarget.style.background =
                                      isSelected
                                        ? "rgba(124, 58, 237, 0.2)"
                                        : "rgba(0, 0, 0, 0.05)";
                                    e.currentTarget.style.boxShadow =
                                      "0 2px 8px rgba(0, 0, 0, 0.08)";
                                  }
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.background = isSelected
                                    ? isDark
                                      ? "rgba(167, 139, 250, 0.2)"
                                      : "rgba(124, 58, 237, 0.15)"
                                    : isDark
                                      ? "rgba(255, 255, 255, 0.05)"
                                      : "rgba(0, 0, 0, 0.03)";
                                  e.currentTarget.style.boxShadow = "none";
                                }}
                              >
                                <div className="flex items-center justify-between">
                                  <span
                                    className="text-sm truncate"
                                    style={{
                                      color: isSelected
                                        ? isDark
                                          ? "#c4b5fd"
                                          : "#7c3aed"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.8)"
                                          : "rgba(0, 0, 0, 0.8)",
                                    }}
                                  >
                                    {repo.name}
                                  </span>
                                  <span
                                    className="text-xs font-medium px-2 py-0.5 rounded-full ml-2"
                                    style={{
                                      background: isSelected
                                        ? isDark
                                          ? "rgba(167, 139, 250, 0.3)"
                                          : "rgba(124, 58, 237, 0.2)"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.1)"
                                          : "rgba(0, 0, 0, 0.08)",
                                      color: isSelected
                                        ? isDark
                                          ? "#c4b5fd"
                                          : "#7c3aed"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.6)"
                                          : "rgba(0, 0, 0, 0.6)",
                                    }}
                                  >
                                    {repo.count}
                                  </span>
                                </div>
                                <div
                                  className="flex items-center gap-2 text-xs truncate mt-0.5"
                                  style={{
                                    color: isDark
                                      ? "rgba(255, 255, 255, 0.4)"
                                      : "rgba(0, 0, 0, 0.4)",
                                  }}
                                >
                                  <span>{repo.owner}</span>
                                  {repo.stars > 0 && (
                                    <>
                                      <span style={{ opacity: 0.5 }}>•</span>
                                      <span className="inline-flex items-center gap-0.5">
                                        <svg
                                          className="w-3 h-3"
                                          style={{ color: "#f59e0b" }}
                                          fill="currentColor"
                                          viewBox="0 0 24 24"
                                          role="img"
                                          aria-label="Star icon"
                                        >
                                          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                                        </svg>
                                        <span>{repo.stars}</span>
                                      </span>
                                    </>
                                  )}
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Blueprint Filter */}
                    {facets.blueprints.length > 0 && (
                      <div>
                        <h3
                          className="text-sm font-semibold mb-3"
                          style={{
                            color: isDark ? "#e0e7ff" : "#1f2937",
                          }}
                        >
                          🎨 Blueprints
                        </h3>
                        <div
                          className="space-y-2 pb-1"
                        >
                          {facets.blueprints.map((blueprint) => {
                            const isSelected =
                              selectedBlueprint === blueprint.path;
                            const displayName =
                              blueprint.path.split("/").pop() || blueprint.path;
                            return (
                              <button
                                key={blueprint.path}
                                type="button"
                                onClick={() =>
                                  setSelectedBlueprint(
                                    isSelected ? null : blueprint.path,
                                  )
                                }
                                className="w-full text-left px-3 py-2 rounded-lg transition-all duration-150"
                                style={{
                                  background: isSelected
                                    ? isDark
                                      ? "rgba(96, 165, 250, 0.2)"
                                      : "rgba(37, 99, 235, 0.15)"
                                    : isDark
                                      ? "rgba(255, 255, 255, 0.05)"
                                      : "rgba(0, 0, 0, 0.03)",
                                  border: isSelected
                                    ? isDark
                                      ? "1px solid rgba(96, 165, 250, 0.4)"
                                      : "1px solid rgba(37, 99, 235, 0.3)"
                                    : isDark
                                      ? "1px solid rgba(255, 255, 255, 0.05)"
                                      : "1px solid rgba(0, 0, 0, 0.05)",
                                }}
                                onMouseEnter={(e) => {
                                  if (isDark) {
                                    e.currentTarget.style.background =
                                      isSelected
                                        ? "rgba(96, 165, 250, 0.3)"
                                        : "rgba(255, 255, 255, 0.1)";
                                    e.currentTarget.style.boxShadow =
                                      "0 4px 12px rgba(0, 0, 0, 0.2)";
                                  } else {
                                    e.currentTarget.style.background =
                                      isSelected
                                        ? "rgba(37, 99, 235, 0.2)"
                                        : "rgba(0, 0, 0, 0.05)";
                                    e.currentTarget.style.boxShadow =
                                      "0 2px 8px rgba(0, 0, 0, 0.08)";
                                  }
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.background = isSelected
                                    ? isDark
                                      ? "rgba(96, 165, 250, 0.2)"
                                      : "rgba(37, 99, 235, 0.15)"
                                    : isDark
                                      ? "rgba(255, 255, 255, 0.05)"
                                      : "rgba(0, 0, 0, 0.03)";
                                  e.currentTarget.style.boxShadow = "none";
                                }}
                              >
                                <div className="flex items-center justify-between">
                                  <span
                                    className="text-sm truncate"
                                    style={{
                                      color: isSelected
                                        ? isDark
                                          ? "#93c5fd"
                                          : "#2563eb"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.8)"
                                          : "rgba(0, 0, 0, 0.8)",
                                    }}
                                    title={blueprint.path}
                                  >
                                    {displayName}
                                  </span>
                                  <span
                                    className="text-xs font-medium px-2 py-0.5 rounded-full ml-2"
                                    style={{
                                      background: isSelected
                                        ? isDark
                                          ? "rgba(96, 165, 250, 0.3)"
                                          : "rgba(37, 99, 235, 0.2)"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.1)"
                                          : "rgba(0, 0, 0, 0.08)",
                                      color: isSelected
                                        ? isDark
                                          ? "#93c5fd"
                                          : "#2563eb"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.6)"
                                          : "rgba(0, 0, 0, 0.6)",
                                    }}
                                  >
                                    {blueprint.count}
                                  </span>
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Trigger Filter */}
                    {facets.triggers.length > 0 && (
                      <div>
                        <h3
                          className="text-sm font-semibold mb-3"
                          style={{
                            color: isDark ? "#e0e7ff" : "#1f2937",
                          }}
                        >
                          ⚡ Triggers
                        </h3>
                        <div
                          className="space-y-2 pb-1"
                        >
                          {facets.triggers.map((trigger) => {
                            const isSelected = selectedTrigger === trigger.type;
                            return (
                              <button
                                key={trigger.type}
                                type="button"
                                onClick={() =>
                                  setSelectedTrigger(
                                    isSelected ? null : trigger.type,
                                  )
                                }
                                className="w-full text-left px-3 py-2 rounded-lg transition-all duration-150"
                                style={{
                                  background: isSelected
                                    ? isDark
                                      ? "rgba(52, 211, 153, 0.2)"
                                      : "rgba(16, 185, 129, 0.15)"
                                    : isDark
                                      ? "rgba(255, 255, 255, 0.05)"
                                      : "rgba(0, 0, 0, 0.03)",
                                  border: isSelected
                                    ? isDark
                                      ? "1px solid rgba(52, 211, 153, 0.4)"
                                      : "1px solid rgba(16, 185, 129, 0.3)"
                                    : isDark
                                      ? "1px solid rgba(255, 255, 255, 0.05)"
                                      : "1px solid rgba(0, 0, 0, 0.05)",
                                }}
                                onMouseEnter={(e) => {
                                  if (isDark) {
                                    e.currentTarget.style.background =
                                      isSelected
                                        ? "rgba(52, 211, 153, 0.3)"
                                        : "rgba(255, 255, 255, 0.1)";
                                    e.currentTarget.style.boxShadow =
                                      "0 4px 12px rgba(0, 0, 0, 0.2)";
                                  } else {
                                    e.currentTarget.style.background =
                                      isSelected
                                        ? "rgba(16, 185, 129, 0.2)"
                                        : "rgba(0, 0, 0, 0.05)";
                                    e.currentTarget.style.boxShadow =
                                      "0 2px 8px rgba(0, 0, 0, 0.08)";
                                  }
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.background = isSelected
                                    ? isDark
                                      ? "rgba(52, 211, 153, 0.2)"
                                      : "rgba(16, 185, 129, 0.15)"
                                    : isDark
                                      ? "rgba(255, 255, 255, 0.05)"
                                      : "rgba(0, 0, 0, 0.03)";
                                  e.currentTarget.style.boxShadow = "none";
                                }}
                              >
                                <div className="flex items-center justify-between">
                                  <span
                                    className="text-sm truncate"
                                    style={{
                                      color: isSelected
                                        ? isDark
                                          ? "#6ee7b7"
                                          : "#10b981"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.8)"
                                          : "rgba(0, 0, 0, 0.8)",
                                    }}
                                  >
                                    {trigger.type}
                                  </span>
                                  <span
                                    className="text-xs font-medium px-2 py-0.5 rounded-full ml-2"
                                    style={{
                                      background: isSelected
                                        ? isDark
                                          ? "rgba(52, 211, 153, 0.3)"
                                          : "rgba(16, 185, 129, 0.2)"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.1)"
                                          : "rgba(0, 0, 0, 0.08)",
                                      color: isSelected
                                        ? isDark
                                          ? "#6ee7b7"
                                          : "#10b981"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.6)"
                                          : "rgba(0, 0, 0, 0.6)",
                                    }}
                                  >
                                    {trigger.count}
                                  </span>
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Action Filter */}
                    {facets.actions.length > 0 && (
                      <div>
                        <h3
                          className="text-sm font-semibold mb-3"
                          style={{
                            color: isDark ? "#e0e7ff" : "#1f2937",
                          }}
                        >
                          🎬 Actions
                        </h3>
                        <div
                          className="space-y-2 pb-1"
                        >
                          {facets.actions.map((action) => {
                            const isSelected = selectedAction === action.call;
                            return (
                              <button
                                key={action.call}
                                type="button"
                                onClick={() =>
                                  setSelectedAction(
                                    isSelected ? null : action.call,
                                  )
                                }
                                className="w-full text-left px-3 py-2 rounded-lg transition-all duration-150"
                                style={{
                                  background: isSelected
                                    ? isDark
                                      ? "rgba(251, 191, 36, 0.2)"
                                      : "rgba(245, 158, 11, 0.15)"
                                    : isDark
                                      ? "rgba(255, 255, 255, 0.05)"
                                      : "rgba(0, 0, 0, 0.03)",
                                  border: isSelected
                                    ? isDark
                                      ? "1px solid rgba(251, 191, 36, 0.4)"
                                      : "1px solid rgba(245, 158, 11, 0.3)"
                                    : isDark
                                      ? "1px solid rgba(255, 255, 255, 0.05)"
                                      : "1px solid rgba(0, 0, 0, 0.05)",
                                }}
                                onMouseEnter={(e) => {
                                  if (isDark) {
                                    e.currentTarget.style.background =
                                      isSelected
                                        ? "rgba(251, 191, 36, 0.3)"
                                        : "rgba(255, 255, 255, 0.1)";
                                    e.currentTarget.style.boxShadow =
                                      "0 4px 12px rgba(0, 0, 0, 0.2)";
                                  } else {
                                    e.currentTarget.style.background =
                                      isSelected
                                        ? "rgba(245, 158, 11, 0.2)"
                                        : "rgba(0, 0, 0, 0.05)";
                                    e.currentTarget.style.boxShadow =
                                      "0 2px 8px rgba(0, 0, 0, 0.08)";
                                  }
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.background = isSelected
                                    ? isDark
                                      ? "rgba(251, 191, 36, 0.2)"
                                      : "rgba(245, 158, 11, 0.15)"
                                    : isDark
                                      ? "rgba(255, 255, 255, 0.05)"
                                      : "rgba(0, 0, 0, 0.03)";
                                  e.currentTarget.style.boxShadow = "none";
                                }}
                              >
                                <div className="flex items-center justify-between">
                                  <span
                                    className="text-sm truncate font-mono"
                                    style={{
                                      color: isSelected
                                        ? isDark
                                          ? "#fbbf24"
                                          : "#d97706"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.8)"
                                          : "rgba(0, 0, 0, 0.8)",
                                    }}
                                  >
                                    {action.call}
                                  </span>
                                  <span
                                    className="text-xs font-medium px-2 py-0.5 rounded-full ml-2"
                                    style={{
                                      background: isSelected
                                        ? isDark
                                          ? "rgba(251, 191, 36, 0.3)"
                                          : "rgba(245, 158, 11, 0.2)"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.1)"
                                          : "rgba(0, 0, 0, 0.08)",
                                      color: isSelected
                                        ? isDark
                                          ? "#fbbf24"
                                          : "#d97706"
                                        : isDark
                                          ? "rgba(255, 255, 255, 0.6)"
                                          : "rgba(0, 0, 0, 0.6)",
                                    }}
                                  >
                                    {action.count}
                                  </span>
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </aside>
            </>
          )}

          {/* Results */}
          <div className="space-y-4 flex-1">
            {loading ? (
              <div className="text-center py-20">
                <div
                  className="inline-flex items-center justify-center w-16 h-16 rounded-full backdrop-blur-xl mb-4"
                  style={{
                    background: isDark
                      ? "rgba(25, 25, 40, 0.6)"
                      : "rgba(0, 0, 0, 0.04)",
                    border: isDark
                      ? "1px solid rgba(255, 255, 255, 0.08)"
                      : "1px solid rgba(0, 0, 0, 0.06)",
                  }}
                >
                  <svg
                    className="animate-spin h-8 w-8"
                    style={{ color: "#12bcf2" }}
                    fill="none"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Loading statistics"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                </div>
                <p
                  className="text-lg"
                  style={{
                    color: isDark
                      ? "rgba(255, 255, 255, 0.5)"
                      : "rgba(0, 0, 0, 0.6)",
                  }}
                >
                  Searching automations...
                </p>
              </div>
            ) : results.length === 0 ? (
              <div
                className="text-center py-20 rounded-3xl backdrop-blur-xl"
                style={{
                  background: isDark
                    ? "rgba(25, 25, 40, 0.6)"
                    : "rgba(255, 255, 255, 0.8)",
                  border: isDark
                    ? "1px solid rgba(255, 255, 255, 0.08)"
                    : "1px solid rgba(0, 0, 0, 0.08)",
                }}
              >
                <div className="text-6xl mb-4">🔍</div>
                <p
                  className="text-xl mb-2"
                  style={{
                    color: isDark
                      ? "rgba(255, 255, 255, 0.7)"
                      : "rgba(0, 0, 0, 0.8)",
                  }}
                >
                  {query ? "No automations found" : "Start your search"}
                </p>
                <p
                  style={{
                    color: isDark
                      ? "rgba(255, 255, 255, 0.4)"
                      : "rgba(0, 0, 0, 0.5)",
                  }}
                >
                  {query
                    ? "Try a different search term or browse all results"
                    : "Search for automations by name, trigger, or action"}
                </p>
              </div>
            ) : (
              results.map((automation) => (
                <article
                  key={automation.id}
                  className="group rounded-3xl backdrop-blur-xl p-8 transition-all duration-200"
                  style={{
                    background: isDark
                      ? "rgba(25, 25, 40, 0.65)"
                      : "rgba(255, 255, 255, 0.8)",
                    border: isDark
                      ? "1px solid rgba(255, 255, 255, 0.08)"
                      : "1px solid rgba(0, 0, 0, 0.08)",
                    boxShadow: isDark
                      ? "0 4px 16px rgba(0, 0, 0, 0.2)"
                      : "0 2px 8px rgba(0, 0, 0, 0.05)",
                  }}
                  onMouseEnter={(e) => {
                    if (isDark) {
                      e.currentTarget.style.background =
                        "rgba(30, 30, 48, 0.75)";
                      e.currentTarget.style.borderColor =
                        "rgba(255, 255, 255, 0.12)";
                      e.currentTarget.style.boxShadow =
                        "0 8px 24px rgba(0, 0, 0, 0.3)";
                    } else {
                      e.currentTarget.style.background =
                        "rgba(255, 255, 255, 0.95)";
                      e.currentTarget.style.boxShadow =
                        "0 4px 16px rgba(0, 0, 0, 0.08)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = isDark
                      ? "rgba(25, 25, 40, 0.65)"
                      : "rgba(255, 255, 255, 0.8)";
                    e.currentTarget.style.borderColor = isDark
                      ? "rgba(255, 255, 255, 0.08)"
                      : "rgba(0, 0, 0, 0.08)";
                    e.currentTarget.style.boxShadow = isDark
                      ? "0 4px 16px rgba(0, 0, 0, 0.2)"
                      : "0 2px 8px rgba(0, 0, 0, 0.05)";
                  }}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4">
                    <div className="flex-1 min-w-0">
                      <a
                        href={getGitHubUrlWithLines(automation)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block group/title"
                      >
                        <h3
                          className="text-2xl font-semibold mb-2 group-hover/title:text-[rgb(var(--ha-blue))] transition-colors line-clamp-2"
                          style={{
                            color: isDark ? "#e0e7ff" : "#1f2937",
                          }}
                        >
                          {automation.alias || "Unnamed Automation"}
                        </h3>
                      </a>
                      <div
                        className="flex flex-wrap items-center gap-2 text-sm"
                        style={{
                          color: isDark
                            ? "rgba(255, 255, 255, 0.45)"
                            : "rgba(0, 0, 0, 0.5)",
                        }}
                      >
                        <a
                          href={automation.repository.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:text-[rgb(var(--ha-blue))] transition-colors font-medium flex items-center gap-1.5"
                        >
                          <span>
                            {automation.repository.owner}/
                            {automation.repository.name}
                          </span>
                          {automation.repository.stars > 0 && (
                            <span className="inline-flex items-center gap-0.5">
                              <svg
                                className="w-3.5 h-3.5"
                                style={{ color: "#f59e0b" }}
                                fill="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Star icon"
                              >
                                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                              </svg>
                              <span>{automation.repository.stars}</span>
                            </span>
                          )}
                        </a>
                        <span style={{ opacity: 0.5 }}>•</span>
                        <span className="font-mono text-xs truncate">
                          {automation.source_file_path}
                        </span>
                      </div>
                    </div>
                    <a
                      href={getGitHubUrlWithLines(automation)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-shrink-0 inline-flex items-center gap-2 px-5 py-2.5 font-medium rounded-xl transition-all duration-200"
                      style={{
                        color: isDark ? "rgba(255, 255, 255, 0.7)" : "#1f2937",
                        background: isDark
                          ? "rgba(255, 255, 255, 0.05)"
                          : "rgba(0, 0, 0, 0.04)",
                        border: isDark
                          ? "1px solid rgba(255, 255, 255, 0.08)"
                          : "1px solid rgba(0, 0, 0, 0.08)",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = isDark
                          ? "rgba(255, 255, 255, 0.08)"
                          : "rgba(0, 0, 0, 0.06)";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = isDark
                          ? "rgba(255, 255, 255, 0.05)"
                          : "rgba(0, 0, 0, 0.04)";
                      }}
                    >
                      <svg
                        className="w-4 h-4"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                        role="img"
                        aria-label="GitHub logo"
                      >
                        <path
                          fillRule="evenodd"
                          d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                          clipRule="evenodd"
                        />
                      </svg>
                      GitHub
                    </a>
                  </div>

                  {automation.description && (
                    <p
                      className="text-base leading-relaxed mb-5"
                      style={{
                        color: isDark
                          ? "rgba(255, 255, 255, 0.55)"
                          : "rgba(0, 0, 0, 0.6)",
                      }}
                    >
                      {automation.description}
                    </p>
                  )}

                  {automation.blueprint_path && (
                    <div className="mb-5">
                      <span
                        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-xl"
                        style={{
                          color: isDark ? "#c4b5fd" : "#6d28d9",
                          background: isDark
                            ? "rgba(109, 40, 217, 0.15)"
                            : "rgba(109, 40, 217, 0.08)",
                          border: isDark
                            ? "1px solid rgba(109, 40, 217, 0.25)"
                            : "1px solid rgba(109, 40, 217, 0.15)",
                        }}
                      >
                        <svg
                          className="w-4 h-4"
                          fill="currentColor"
                          viewBox="0 0 24 24"
                          role="img"
                          aria-label="Blueprint icon"
                        >
                          <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z" />
                        </svg>
                        Blueprint: {automation.blueprint_path}
                      </span>
                    </div>
                  )}

                  <div className="space-y-4">
                    {automation.trigger_types.length > 0 && (
                      <div>
                        <p
                          className="text-xs font-semibold uppercase tracking-wider mb-2"
                          style={{
                            color: isDark
                              ? "rgba(255, 255, 255, 0.4)"
                              : "rgba(0, 0, 0, 0.4)",
                          }}
                        >
                          Triggers
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {automation.trigger_types.map((trigger) => (
                            <span
                              key={trigger}
                              className="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-full backdrop-blur-sm"
                              style={{
                                color: "#12bcf2",
                                background: isDark
                                  ? "rgba(18, 188, 242, 0.12)"
                                  : "rgba(18, 188, 242, 0.1)",
                                border: isDark
                                  ? "1px solid rgba(18, 188, 242, 0.2)"
                                  : "1px solid rgba(18, 188, 242, 0.15)",
                              }}
                            >
                              {trigger}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {automation.action_calls &&
                      automation.action_calls.length > 0 && (
                        <div>
                          <p
                            className="text-xs font-semibold uppercase tracking-wider mb-2"
                            style={{
                              color: isDark
                                ? "rgba(255, 255, 255, 0.4)"
                                : "rgba(0, 0, 0, 0.4)",
                            }}
                          >
                            Actions
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {automation.action_calls.map((action) => (
                              <span
                                key={action}
                                className="px-3 py-1.5 text-xs font-mono rounded-lg backdrop-blur-sm"
                                style={{
                                  color: isDark ? "#6ee7b7" : "#059669",
                                  background: isDark
                                    ? "rgba(16, 185, 129, 0.12)"
                                    : "rgba(16, 185, 129, 0.08)",
                                  border: isDark
                                    ? "1px solid rgba(16, 185, 129, 0.2)"
                                    : "1px solid rgba(16, 185, 129, 0.15)",
                                }}
                              >
                                {action}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>
                </article>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-24 mb-12">
          <div
            className="rounded-3xl backdrop-blur-xl p-8 text-center"
            style={{
              background: isDark
                ? "rgba(25, 25, 40, 0.6)"
                : "rgba(255, 255, 255, 0.8)",
              border: isDark
                ? "1px solid rgba(255, 255, 255, 0.08)"
                : "1px solid rgba(0, 0, 0, 0.08)",
            }}
          >
            <div className="max-w-2xl mx-auto">
              <h3
                className="text-lg font-semibold mb-3"
                style={{
                  color: isDark ? "#e0e7ff" : "#1f2937",
                }}
              >
                Want to be discovered?
              </h3>
              <p
                className="mb-4 leading-relaxed"
                style={{
                  color: isDark
                    ? "rgba(255, 255, 255, 0.55)"
                    : "rgba(0, 0, 0, 0.6)",
                }}
              >
                hadiscover indexes Home Assistant automations from GitHub
                repositories with the{" "}
                <code
                  className="px-2 py-1 rounded-lg font-mono text-sm"
                  style={{
                    color: "#12bcf2",
                    background: isDark
                      ? "rgba(18, 188, 242, 0.12)"
                      : "rgba(18, 188, 242, 0.08)",
                  }}
                >
                  hadiscover
                </code>{" "}
                topic.
              </p>
              <p
                className="text-sm"
                style={{
                  color: isDark
                    ? "rgba(255, 255, 255, 0.4)"
                    : "rgba(0, 0, 0, 0.5)",
                }}
              >
                Add the topic to your repository to share your automations with
                the community!
              </p>
            </div>
          </div>

          {/* How to Add Automations Section */}
          <div className="mt-8">
            <details
              className="rounded-3xl backdrop-blur-xl overflow-hidden transition-all duration-200"
              style={{
                background: isDark
                  ? "rgba(25, 25, 40, 0.6)"
                  : "rgba(255, 255, 255, 0.8)",
                border: isDark
                  ? "1px solid rgba(255, 255, 255, 0.08)"
                  : "1px solid rgba(0, 0, 0, 0.08)",
              }}
            >
              <summary
                className="px-8 py-6 cursor-pointer list-none transition-all duration-200 hover:bg-opacity-90"
                style={{
                  color: isDark ? "#e0e7ff" : "#1f2937",
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">🏠</span>
                    <div>
                      <h3 className="text-lg font-semibold">
                        How to Add Automations to Home Assistant
                      </h3>
                      <p
                        className="text-sm mt-1"
                        style={{
                          color: isDark
                            ? "rgba(255, 255, 255, 0.5)"
                            : "rgba(0, 0, 0, 0.5)",
                        }}
                      >
                        Copy YAML and add to your instance
                      </p>
                    </div>
                  </div>
                  <svg
                    className="w-5 h-5 transition-transform duration-200"
                    style={{
                      color: isDark
                        ? "rgba(255, 255, 255, 0.5)"
                        : "rgba(0, 0, 0, 0.5)",
                    }}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Expand section"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
              </summary>
              <div
                className="px-8 pb-8 pt-4 border-t"
                style={{
                  borderColor: isDark
                    ? "rgba(255, 255, 255, 0.08)"
                    : "rgba(0, 0, 0, 0.08)",
                }}
              >
                <p
                  className="mb-4 leading-relaxed"
                  style={{
                    color: isDark
                      ? "rgba(255, 255, 255, 0.6)"
                      : "rgba(0, 0, 0, 0.7)",
                  }}
                >
                  Found an automation you like? Here's how to add it to your
                  Home Assistant:
                </p>
                <ol
                  className="list-decimal list-inside space-y-3 mb-6"
                  style={{
                    color: isDark
                      ? "rgba(255, 255, 255, 0.6)"
                      : "rgba(0, 0, 0, 0.7)",
                  }}
                >
                  <li>
                    <strong>Copy the YAML</strong> - Click on the GitHub link
                    for any automation and copy its YAML code
                  </li>
                  <li>
                    <strong>Open Home Assistant</strong> - Go to Settings →
                    Automations & Scenes → Create Automation
                  </li>
                  <li>
                    <strong>Paste the code</strong> - Click the three-dot menu →
                    Edit in YAML, then paste your code
                  </li>
                  <li>
                    <strong>Customize</strong> - Update entity names and
                    settings to match your setup
                  </li>
                  <li>
                    <strong>Save</strong> - Save your automation and test it!
                  </li>
                </ol>
                <div className="flex flex-col sm:flex-row gap-3">
                  <a
                    href="https://my.home-assistant.io/redirect/automations/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-200"
                    style={{
                      background: isDark
                        ? "linear-gradient(135deg, rgba(18, 188, 242, 0.8), rgba(14, 165, 233, 0.8))"
                        : "linear-gradient(135deg, rgb(18, 188, 242), rgb(14, 165, 233))",
                      color: "#ffffff",
                      border: isDark
                        ? "1px solid rgba(18, 188, 242, 0.3)"
                        : "none",
                      boxShadow: isDark
                        ? "0 4px 12px rgba(18, 188, 242, 0.25)"
                        : "0 4px 12px rgba(18, 188, 242, 0.3)",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = "translateY(-1px)";
                      e.currentTarget.style.boxShadow = isDark
                        ? "0 6px 16px rgba(18, 188, 242, 0.35)"
                        : "0 6px 16px rgba(18, 188, 242, 0.4)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = "translateY(0)";
                      e.currentTarget.style.boxShadow = isDark
                        ? "0 4px 12px rgba(18, 188, 242, 0.25)"
                        : "0 4px 12px rgba(18, 188, 242, 0.3)";
                    }}
                  >
                    <svg
                      className="w-5 h-5"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                      role="img"
                      aria-label="Home Assistant logo"
                    >
                      <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" />
                    </svg>
                    Open Home Assistant Automations
                  </a>
                  <a
                    href="https://www.home-assistant.io/docs/automation/editor/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-medium transition-all duration-200"
                    style={{
                      color: isDark
                        ? "rgba(255, 255, 255, 0.7)"
                        : "rgba(0, 0, 0, 0.7)",
                      background: isDark
                        ? "rgba(255, 255, 255, 0.05)"
                        : "rgba(0, 0, 0, 0.04)",
                      border: isDark
                        ? "1px solid rgba(255, 255, 255, 0.08)"
                        : "1px solid rgba(0, 0, 0, 0.08)",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = isDark
                        ? "rgba(255, 255, 255, 0.08)"
                        : "rgba(0, 0, 0, 0.06)";
                      e.currentTarget.style.transform = "translateY(-1px)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = isDark
                        ? "rgba(255, 255, 255, 0.05)"
                        : "rgba(0, 0, 0, 0.04)";
                      e.currentTarget.style.transform = "translateY(0)";
                    }}
                  >
                    📚 View Documentation
                  </a>
                </div>
              </div>
            </details>
          </div>

          {/* GPT Prompt Section */}
          <div className="mt-8">
            <details
              className="rounded-3xl backdrop-blur-xl overflow-hidden transition-all duration-200"
              style={{
                background: isDark
                  ? "rgba(25, 25, 40, 0.6)"
                  : "rgba(255, 255, 255, 0.8)",
                border: isDark
                  ? "1px solid rgba(255, 255, 255, 0.08)"
                  : "1px solid rgba(0, 0, 0, 0.08)",
              }}
            >
              <summary
                className="px-8 py-6 cursor-pointer list-none transition-all duration-200 hover:bg-opacity-90"
                style={{
                  color: isDark ? "#e0e7ff" : "#1f2937",
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">✨</span>
                    <div>
                      <h3 className="text-lg font-semibold">
                        Improve Your Automations with AI
                      </h3>
                      <p
                        className="text-sm mt-1"
                        style={{
                          color: isDark
                            ? "rgba(255, 255, 255, 0.5)"
                            : "rgba(0, 0, 0, 0.5)",
                        }}
                      >
                        GPT prompt to write better titles & descriptions
                      </p>
                    </div>
                  </div>
                  <svg
                    className="w-5 h-5 transition-transform duration-200"
                    style={{
                      color: isDark
                        ? "rgba(255, 255, 255, 0.5)"
                        : "rgba(0, 0, 0, 0.5)",
                    }}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Expand section"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
              </summary>
              <div
                className="px-8 pb-8 pt-4 border-t"
                style={{
                  borderColor: isDark
                    ? "rgba(255, 255, 255, 0.08)"
                    : "rgba(0, 0, 0, 0.08)",
                }}
              >
                <p
                  className="mb-4 leading-relaxed"
                  style={{
                    color: isDark
                      ? "rgba(255, 255, 255, 0.6)"
                      : "rgba(0, 0, 0, 0.7)",
                  }}
                >
                  Clear titles and descriptions make your automations more
                  discoverable. Copy this prompt and your automation YAML to
                  ChatGPT, Claude, or any AI assistant:
                </p>
                <div className="relative group">
                  <pre
                    className="rounded-2xl p-6 overflow-x-auto text-sm leading-relaxed"
                    style={{
                      background: isDark
                        ? "rgba(17, 17, 27, 0.8)"
                        : "rgba(248, 248, 248, 0.95)",
                      color: isDark ? "#e0e7ff" : "#1f2937",
                      border: isDark
                        ? "1px solid rgba(255, 255, 255, 0.08)"
                        : "1px solid rgba(0, 0, 0, 0.08)",
                    }}
                  >
                    <code>{`You are reviewing a Home Assistant automations.yaml file.

For each automation, rewrite:

1. alias (title)
• Max 10 words
• Clear, simple, no technical jargon
• Understandable by someone with no Home Assistant knowledge

2. description
• Max 4 short lines
• Plain, everyday language
• Explain what happens, when, and why, from a user’s perspective
• Avoid technical terms like trigger, entity, service, state, automation

Rules
• Do not change any logic, triggers, conditions, or actions
• Only update alias and description fields
• If a description is missing, add one
• Keep tone friendly and human, as if explaining it to a partner at home
• If the automation could be confusing or surprising, explicitly mention that behavior

Here's my automation YAML:

[Paste your automation YAML here]`}</code>
                  </pre>
                  <button
                    type="button"
                    onClick={() => {
                      const text = `You are reviewing a Home Assistant automations.yaml file.

For each automation, rewrite:

1. alias (title)
• Max 10 words
• Clear, simple, no technical jargon
• Understandable by someone with no Home Assistant knowledge

2. description
• Max 4 short lines
• Plain, everyday language
• Explain what happens, when, and why, from a user’s perspective
• Avoid technical terms like trigger, entity, service, state, automation

Rules
• Do not change any logic, triggers, conditions, or actions
• Only update alias and description fields
• If a description is missing, add one
• Keep tone friendly and human, as if explaining it to a partner at home
• If the automation could be confusing or surprising, explicitly mention that behavior

Here's my automation YAML:

[Paste your automation YAML here]`;
                      navigator.clipboard.writeText(text);
                      setCopied(true);
                      setTimeout(() => setCopied(false), 2000);
                    }}
                    className="absolute top-4 right-4 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 opacity-0 group-hover:opacity-100"
                    style={{
                      background: copied
                        ? isDark
                          ? "rgba(34, 197, 94, 0.8)"
                          : "rgb(34, 197, 94)"
                        : isDark
                          ? "rgba(109, 40, 217, 0.8)"
                          : "rgb(109, 40, 217)",
                      color: "#ffffff",
                      border: copied
                        ? isDark
                          ? "1px solid rgba(34, 197, 94, 0.3)"
                          : "none"
                        : isDark
                          ? "1px solid rgba(147, 51, 234, 0.3)"
                          : "none",
                    }}
                  >
                    {copied ? "✓ Copied!" : "📋 Copy"}
                  </button>
                </div>
              </div>
            </details>
          </div>

          {/* Repository Info */}
          {statistics && (
            <div className="text-center mt-6">
              <a
                href="https://github.com/DevSecNinja/hadiscover"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl transition-all duration-200"
                style={{
                  color: isDark ? "rgba(255, 255, 255, 0.7)" : "#1f2937",
                  background: isDark
                    ? "rgba(255, 255, 255, 0.05)"
                    : "rgba(0, 0, 0, 0.04)",
                  border: isDark
                    ? "1px solid rgba(255, 255, 255, 0.08)"
                    : "1px solid rgba(0, 0, 0, 0.08)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = isDark
                    ? "rgba(255, 255, 255, 0.08)"
                    : "rgba(0, 0, 0, 0.06)";
                  e.currentTarget.style.transform = "translateY(-1px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = isDark
                    ? "rgba(255, 255, 255, 0.05)"
                    : "rgba(0, 0, 0, 0.04)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  role="img"
                  aria-label="GitHub logo"
                >
                  <path
                    fillRule="evenodd"
                    d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="font-medium">DevSecNinja/hadiscover</span>
                <span className="flex items-center gap-1">
                  <svg
                    className="w-4 h-4"
                    style={{ color: "#f59e0b" }}
                    fill="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Star icon"
                  >
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                  </svg>
                  {statistics.repo_star_count}
                </span>
              </a>
              <p
                className="text-sm mt-3"
                style={{
                  color: isDark
                    ? "rgba(255, 255, 255, 0.4)"
                    : "rgba(0, 0, 0, 0.5)",
                }}
              >
                ⭐ Star us on GitHub to show your support!
              </p>
            </div>
          )}

          <div
            className="text-center mt-6 text-sm"
            style={{
              color: isDark ? "rgba(255, 255, 255, 0.3)" : "rgba(0, 0, 0, 0.4)",
            }}
          >
            <p>Built with 💙 for the Home Assistant community</p>
          </div>

          {statistics?.last_indexed_at && (
            <div className="text-center mt-6">
              <p
                className="text-sm"
                style={{
                  color: isDark
                    ? "rgba(255, 255, 255, 0.3)"
                    : "rgba(0, 0, 0, 0.4)",
                }}
              >
                Last indexed: {formatLastIndexed(statistics.last_indexed_at)}
              </p>
            </div>
          )}
        </footer>
      </div>
    </div>
  );
}
