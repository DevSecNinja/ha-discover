'use client';

import { useState, useEffect } from 'react';

interface Repository {
  name: string;
  owner: string;
  description: string | null;
  url: string;
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
  repository: Repository;
  indexed_at: string | null;
}

interface SearchResponse {
  query: string;
  results: Automation[];
  count: number;
}

interface Statistics {
  total_repositories: number;
  total_automations: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
const IS_DEVELOPMENT = process.env.NODE_ENV === 'development';

if (!API_BASE_URL) {
  console.error('NEXT_PUBLIC_API_URL environment variable is not set');
}

if (IS_DEVELOPMENT) {
  console.info('🚧 Running in development mode');
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Automation[]>([]);
  const [loading, setLoading] = useState(false);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [indexing, setIndexing] = useState(false);

  useEffect(() => {
    // Load statistics on mount
    fetchStatistics();
    // Load initial results
    performSearch('');
  }, []);

  const fetchStatistics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/statistics`);
      const data = await response.json();
      setStatistics(data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const performSearch = async (searchQuery: string) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(searchQuery)}`);
      const data: SearchResponse = await response.json();
      setResults(data.results);
    } catch (error) {
      console.error('Error searching:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query);
  };

  const handleTriggerIndexing = async () => {
    setIndexing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/index`, {
        method: 'POST',
      });

      if (response.status === 429) {
        const data = await response.json();
        alert(`Rate limit exceeded: ${data.detail}`);
      } else if (response.ok) {
        const data = await response.json();
        if (data.started) {
          alert('Indexing started! This may take a few minutes. Refresh the page to see updated results.');
        }
      } else {
        alert('Failed to trigger indexing');
      }
    } catch (error) {
      console.error('Error triggering indexing:', error);
      alert('Failed to trigger indexing');
    } finally {
      setIndexing(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 gradient-bg -z-10"></div>
      <div className="fixed inset-0 -z-10" style={{
        background: 'radial-gradient(ellipse at top, rgba(124, 58, 237, 0.2), transparent)'
      }}></div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <header className="text-center mb-16 pt-8">
          <div className="inline-flex items-center gap-3 mb-6 px-4 py-2 rounded-full glass border" style={{ borderColor: 'rgba(255, 255, 255, 0.2)' }}>
            <svg className="w-5 h-5 text-[rgb(var(--ha-blue))]" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
            </svg>
            <span className="text-sm font-medium text-white" style={{ opacity: 0.9 }}>Home Assistant Discovery</span>
          </div>

          <h1 className="text-7xl sm:text-8xl font-bold mb-6 tracking-tight">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-100 to-purple-200 drop-shadow-2xl">
              hadiscover
            </span>
          </h1>

          <p className="text-2xl sm:text-3xl text-white mb-4 font-light max-w-3xl mx-auto leading-relaxed" style={{ opacity: 0.8 }}>
            Discover and explore powerful automations
          </p>

          {statistics && (
            <div className="flex items-center justify-center gap-8 mt-8">
              <div className="glass rounded-2xl px-6 py-4 backdrop-blur-md">
                <div className="text-3xl font-bold text-white mb-1">
                  {statistics.total_automations.toLocaleString()}
                </div>
                <div className="text-sm text-white" style={{ opacity: 0.6 }}>Automations</div>
              </div>
              <div className="glass rounded-2xl px-6 py-4 backdrop-blur-md">
                <div className="text-3xl font-bold text-white mb-1">
                  {statistics.total_repositories.toLocaleString()}
                </div>
                <div className="text-sm text-white" style={{ opacity: 0.6 }}>Repositories</div>
              </div>
            </div>
          )}
        </header>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="mb-16">
          <div className="flex flex-col sm:flex-row gap-3 max-w-4xl mx-auto">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                <svg className="w-5 h-5 text-white" style={{ opacity: 0.4 }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search automations, triggers, actions..."
                className="w-full pl-12 pr-6 py-5 text-lg text-white rounded-2xl border focus:outline-none focus:ring-2 focus:ring-[rgb(var(--ha-blue))] focus:border-transparent transition-all duration-200"
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  backdropFilter: 'blur(24px)',
                  borderColor: 'rgba(255, 255, 255, 0.2)',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-8 py-5 bg-gradient-to-r from-[rgb(var(--ha-blue))] to-blue-500 text-white font-semibold rounded-2xl shadow-xl focus:outline-none focus:ring-2 focus:ring-[rgb(var(--ha-blue))] focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
              style={{ boxShadow: '0 20px 25px -5px rgba(59, 130, 246, 0.25)' }}
              onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 25px 50px -12px rgba(59, 130, 246, 0.4)'}
              onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 20px 25px -5px rgba(59, 130, 246, 0.25)'}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Searching
                </span>
              ) : (
                'Search'
              )}
            </button>
          </div>
        </form>

        {/* Indexing Button - Only in development */}
        {IS_DEVELOPMENT && (
          <div className="text-center mb-12">
            <button
              onClick={handleTriggerIndexing}
              disabled={indexing}
              className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-medium rounded-xl shadow-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:scale-[1.02]"
              style={{ boxShadow: '0 10px 15px -3px rgba(34, 197, 94, 0.25)' }}
              onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 20px 25px -5px rgba(34, 197, 94, 0.4)'}
              onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 10px 15px -3px rgba(34, 197, 94, 0.25)'}
            >
              {indexing ? 'Starting Indexing...' : '🔄 Trigger Re-Index'}
            </button>
            <p className="text-sm text-white mt-3" style={{ opacity: 0.6 }}>
              Discover repositories with <code className="px-2 py-1 rounded-lg text-[rgb(var(--ha-blue))] font-mono text-xs" style={{ background: 'rgba(255, 255, 255, 0.1)' }}>hadiscover</code> or <code className="px-2 py-1 rounded-lg text-[rgb(var(--ha-blue))] font-mono text-xs" style={{ background: 'rgba(255, 255, 255, 0.1)' }}>ha-discover</code> topic
            </p>
          </div>
        )}

        {/* Results */}
        <div className="space-y-5">
          {loading ? (
            <div className="text-center py-20">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full backdrop-blur-xl mb-4" style={{ background: 'rgba(255, 255, 255, 0.1)' }}>
                <svg className="animate-spin h-8 w-8 text-[rgb(var(--ha-blue))]" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <p className="text-lg text-white" style={{ opacity: 0.7 }}>Searching automations...</p>
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-20 glass rounded-3xl backdrop-blur-xl">
              <div className="text-6xl mb-4">🔍</div>
              <p className="text-xl text-white mb-2" style={{ opacity: 0.8 }}>
                {query ? 'No automations found' : 'Start your search'}
              </p>
              <p className="text-white" style={{ opacity: 0.5 }}>
                {query ? 'Try a different search term or browse all results' : 'Search for automations by name, trigger, or action'}
              </p>
            </div>
          ) : (
            results.map((automation) => (
              <div
                key={automation.id}
                className="group glass rounded-3xl backdrop-blur-xl p-8 transition-all duration-300 hover:scale-[1.01]"
                style={{
                  boxShadow: '0 0 0 0 rgba(124, 58, 237, 0)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)';
                  e.currentTarget.style.boxShadow = '0 25px 50px -12px rgba(124, 58, 237, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
                  e.currentTarget.style.boxShadow = '0 0 0 0 rgba(124, 58, 237, 0)';
                }}
              >
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4">
                  <div className="flex-1 min-w-0">
                    <a
                      href={automation.github_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block group/title"
                    >
                      <h3 className="text-2xl font-semibold text-white mb-2 group-hover/title:text-[rgb(var(--ha-blue))] transition-colors truncate">
                        {automation.alias || 'Unnamed Automation'}
                      </h3>
                    </a>
                    <div className="flex flex-wrap items-center gap-2 text-sm text-white" style={{ opacity: 0.6 }}>
                      <a
                        href={automation.repository.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-[rgb(var(--ha-blue))] transition-colors font-medium"
                      >
                        {automation.repository.owner}/{automation.repository.name}
                      </a>
                      <span className="text-white" style={{ opacity: 0.3 }}>•</span>
                      <span className="font-mono text-xs truncate">{automation.source_file_path}</span>
                    </div>
                  </div>
                  <a
                    href={automation.github_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 inline-flex items-center gap-2 px-5 py-3 text-white font-medium rounded-xl transition-all duration-200 hover:scale-105 border"
                    style={{
                      background: 'rgba(255, 255, 255, 0.1)',
                      borderColor: 'rgba(255, 255, 255, 0.2)'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                    </svg>
                    GitHub
                  </a>
                </div>

                {automation.description && (
                  <p className="text-white text-base leading-relaxed mb-5" style={{ opacity: 0.7 }}>
                    {automation.description}
                  </p>
                )}

                {automation.blueprint_path && (
                  <div className="mb-5">
                    <span className="inline-flex items-center gap-2 px-4 py-2 text-purple-200 text-sm font-medium rounded-xl border" style={{
                      background: 'linear-gradient(to right, rgba(168, 85, 247, 0.2), rgba(236, 72, 153, 0.2))',
                      borderColor: 'rgba(192, 132, 252, 0.3)'
                    }}>
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
                      </svg>
                      Blueprint: {automation.blueprint_path}
                    </span>
                  </div>
                )}

                <div className="space-y-4">
                  {automation.trigger_types.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-white uppercase tracking-wider mb-2" style={{ opacity: 0.5 }}>Triggers</p>
                      <div className="flex flex-wrap gap-2">
                        {automation.trigger_types.map((trigger, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-3 py-1.5 text-[rgb(var(--ha-blue))] text-xs font-medium rounded-full backdrop-blur-sm border"
                            style={{
                              background: 'rgba(18, 188, 242, 0.2)',
                              borderColor: 'rgba(18, 188, 242, 0.3)'
                            }}
                          >
                            {trigger}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {automation.action_calls && automation.action_calls.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-white uppercase tracking-wider mb-2" style={{ opacity: 0.5 }}>Actions</p>
                      <div className="flex flex-wrap gap-2">
                        {automation.action_calls.map((action, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1.5 text-emerald-300 text-xs font-mono rounded-lg backdrop-blur-sm border"
                            style={{
                              background: 'rgba(16, 185, 129, 0.2)',
                              borderColor: 'rgba(52, 211, 153, 0.3)'
                            }}
                          >
                            {action}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <footer className="mt-24 mb-12">
          <div className="glass rounded-3xl backdrop-blur-xl p-8 text-center">
            <div className="max-w-2xl mx-auto">
              <h3 className="text-lg font-semibold text-white mb-3">Want to be discovered?</h3>
              <p className="text-white mb-4 leading-relaxed" style={{ opacity: 0.7 }}>
                hadiscover indexes Home Assistant automations from GitHub repositories with the{' '}
                <code className="px-2 py-1 rounded-lg text-[rgb(var(--ha-blue))] font-mono text-sm" style={{ background: 'rgba(255, 255, 255, 0.1)' }}>hadiscover</code> or{' '}
                <code className="px-2 py-1 rounded-lg text-[rgb(var(--ha-blue))] font-mono text-sm" style={{ background: 'rgba(255, 255, 255, 0.1)' }}>ha-discover</code> topic.
              </p>
              <p className="text-white text-sm" style={{ opacity: 0.6 }}>
                Add the topic to your repository to share your automations with the community!
              </p>
            </div>
          </div>

          <div className="text-center mt-8 text-white text-sm" style={{ opacity: 0.4 }}>
            <p>Built with 💙 for the Home Assistant community</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
