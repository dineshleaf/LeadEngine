import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Plus, CheckCircle, Globe } from 'lucide-react'
import toast from 'react-hot-toast'
import { searchDomains, importDomains } from '../api/discovery'
import type { DiscoveryResult } from '../types'

export default function DiscoveryPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<DiscoveryResult[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const queryClient = useQueryClient()

  const searchMutation = useMutation({
    mutationFn: () => searchDomains(query),
    onSuccess: (data) => {
      setResults(data)
      setSelected(new Set())
      if (data.length === 0) toast('No results found', { icon: '!' })
    },
    onError: () => toast.error('Search failed'),
  })

  const importMutation = useMutation({
    mutationFn: importDomains,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success(`Imported ${data.length} lead(s)`)
      setResults([])
      setSelected(new Set())
    },
    onError: () => toast.error('Import failed'),
  })

  const toggleSelect = (domain: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(domain)) next.delete(domain)
      else next.add(domain)
      return next
    })
  }

  const selectAll = () => {
    if (selected.size === results.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(results.map((r) => r.domain)))
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Discovery</h1>
        <p className="text-gray-500 mt-1">
          Search for e-commerce businesses to add to your pipeline
        </p>
      </div>

      {/* Search form */}
      <div className="mb-6 rounded-xl bg-white p-6 border border-gray-200 shadow-sm">
        <label className="mb-2 block text-sm font-medium text-gray-700">Search Query</label>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && searchMutation.mutate()}
              placeholder='e.g. "shopify stores selling pet supplies" or "e-commerce fashion brand USA"'
              className="w-full rounded-lg border border-gray-300 py-2.5 pl-10 pr-4 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={() => searchMutation.mutate()}
            disabled={!query.trim() || searchMutation.isPending}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {searchMutation.isPending ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Search
          </button>
        </div>
        <p className="mt-2 text-xs text-gray-400">
          Tip: Use specific queries like industry + platform + location for better results
        </p>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="rounded-xl bg-white border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between border-b px-6 py-4">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold">Results ({results.length})</h2>
              <button onClick={selectAll} className="text-sm text-blue-600 hover:underline">
                {selected.size === results.length ? 'Deselect all' : 'Select all'}
              </button>
            </div>
            {selected.size > 0 && (
              <button
                onClick={() => importMutation.mutate(Array.from(selected))}
                disabled={importMutation.isPending}
                className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              >
                <Plus className="h-4 w-4" />
                Import {selected.size} selected
              </button>
            )}
          </div>

          <div className="divide-y">
            {results.map((result) => (
              <div
                key={result.domain}
                className="flex items-center gap-4 px-6 py-3 hover:bg-gray-50 cursor-pointer"
                onClick={() => toggleSelect(result.domain)}
              >
                <input
                  type="checkbox"
                  checked={selected.has(result.domain)}
                  onChange={() => toggleSelect(result.domain)}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <Globe className="h-5 w-5 text-gray-400" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900">{result.domain}</p>
                  <p className="text-xs text-gray-500 truncate">{result.url}</p>
                </div>
                {selected.has(result.domain) && (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
