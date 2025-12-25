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
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
            hadiscover
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-2">
            Search Home Assistant Automations from GitHub
          </p>
          {statistics && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {statistics.total_automations} automations from {statistics.total_repositories} repositories
            </p>
          )}
        </header>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="flex gap-2 max-w-3xl mx-auto">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search automations by name, description, or trigger type..."
              className="flex-1 px-6 py-4 text-lg border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:border-gray-600 dark:text-white"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-8 py-4 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </form>

        {/* Indexing Button - Only in development */}
        {IS_DEVELOPMENT && (
          <div className="text-center mb-8">
            <button
              onClick={handleTriggerIndexing}
              disabled={indexing}
              className="px-6 py-2 bg-green-600 text-white font-medium rounded-md shadow hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {indexing ? 'Starting Indexing...' : 'Trigger Re-Index'}
            </button>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Discover new repositories with the <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">hadiscover</code> or <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">ha-discover</code> topic
            </p>
          </div>
        )}

        {/* Results */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Searching...</p>
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
              <p className="text-gray-600 dark:text-gray-400">
                {query ? 'No automations found. Try a different search term.' : 'No automations indexed yet. Trigger indexing to get started.'}
              </p>
            </div>
          ) : (
            results.map((automation) => (
              <div
                key={automation.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-200 dark:border-gray-700"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <a
                      href={automation.github_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xl font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      <h3 className="mb-1 hover:underline">
                        {automation.alias || 'Unnamed Automation'}
                      </h3>
                    </a>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      <a
                        href={automation.repository.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:underline text-blue-600 dark:text-blue-400"
                      >
                        {automation.repository.owner}/{automation.repository.name}
                      </a>
                      {' • '}
                      <span className="text-gray-500">{automation.source_file_path}</span>
                    </p>
                  </div>
                  <a
                    href={automation.github_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-4 px-4 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm font-medium rounded-md hover:bg-gray-800 dark:hover:bg-gray-600 transition-colors"
                  >
                    View on GitHub
                  </a>
                </div>

                {automation.description && (
                  <p className="text-gray-700 dark:text-gray-300 mb-3">
                    {automation.description}
                  </p>
                )}

                {automation.blueprint_path && (
                  <div className="mb-3">
                    <span className="inline-flex items-center px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-sm font-medium rounded-md">
                      📘 Blueprint: {automation.blueprint_path}
                    </span>
                  </div>
                )}

                {automation.action_calls && automation.action_calls.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Actions:</p>
                    <div className="flex flex-wrap gap-2">
                      {automation.action_calls.map((action, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs font-mono rounded"
                        >
                          {action}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {automation.trigger_types.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Triggers:</p>
                    <div className="flex flex-wrap gap-2">
                      {automation.trigger_types.map((trigger, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs font-medium rounded-full"
                        >
                          {trigger}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <footer className="mt-16 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>
            hadiscover indexes Home Assistant automations from GitHub repositories with the{' '}
            <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">hadiscover</code> or{' '}
            <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">ha-discover</code> topic.
          </p>
          <p className="mt-2">
            Add the topic to your repository to have your automations indexed!
          </p>
        </footer>
      </div>
    </div>
  );
}
