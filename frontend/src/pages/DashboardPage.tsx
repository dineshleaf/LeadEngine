import { useQuery } from '@tanstack/react-query'
import { BarChart3, Globe, TrendingUp, AlertTriangle, CheckCircle, Clock, XCircle } from 'lucide-react'
import { getStats } from '../api/leads'
import type { Stats } from '../types'

function StatCard({ label, value, icon: Icon, color }: {
  label: string
  value: number
  icon: React.ElementType
  color: string
}) {
  return (
    <div className="flex items-center gap-4 rounded-xl bg-white p-6 shadow-sm border border-gray-100">
      <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${color}`}>
        <Icon className="h-6 w-6 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery<Stats>({
    queryKey: ['stats'],
    queryFn: getStats,
    refetchInterval: 10000,
  })

  if (isLoading || !stats) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Overview of your lead generation pipeline</p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Leads" value={stats.total_leads} icon={Globe} color="bg-blue-500" />
        <StatCard label="Analyzed" value={stats.analyzed} icon={CheckCircle} color="bg-green-500" />
        <StatCard label="E-commerce Confirmed" value={stats.ecommerce_confirmed} icon={TrendingUp} color="bg-purple-500" />
        <StatCard label="With Gaps Found" value={stats.with_gaps} icon={AlertTriangle} color="bg-orange-500" />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-3">
        <StatCard label="Pending" value={stats.pending} icon={Clock} color="bg-gray-400" />
        <StatCard label="Analyzing" value={stats.analyzing} icon={BarChart3} color="bg-yellow-500" />
        <StatCard label="Failed" value={stats.failed} icon={XCircle} color="bg-red-500" />
      </div>

      <div className="mt-10 rounded-xl bg-white p-6 shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold mb-4">Quick Start</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-lg border border-gray-200 p-4">
            <h3 className="font-medium text-gray-900 mb-2">1. Add Leads</h3>
            <p className="text-sm text-gray-500">
              Go to the Leads page to add domains manually, upload a CSV file,
              or use Discovery to find e-commerce businesses automatically.
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 p-4">
            <h3 className="font-medium text-gray-900 mb-2">2. Run Analysis</h3>
            <p className="text-sm text-gray-500">
              Select leads and trigger analysis. The engine will check their e-commerce platform,
              marketing tools, hosting, ads, social media, and find contacts.
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 p-4">
            <h3 className="font-medium text-gray-900 mb-2">3. Export & Pitch</h3>
            <p className="text-sm text-gray-500">
              Export your analyzed leads to CSV/Excel with all data including
              auto-generated personalized pitches for each lead.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
