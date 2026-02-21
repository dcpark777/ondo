'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { getDashboardSummary, getDashboardTrends, getPopularDatasets, DashboardSummary, DashboardTrends, PopularDataset } from './api/client'
import { getStatusBadgeClass, getStatusLabel, getDimensionLabel } from './lib/dataset-utils'

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [trends, setTrends] = useState<DashboardTrends | null>(null)
  const [popular, setPopular] = useState<PopularDataset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const [summaryData, trendsData] = await Promise.all([
          getDashboardSummary(),
          getDashboardTrends(30),
        ])
        setSummary(summaryData)
        setTrends(trendsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
    getPopularDatasets(30, 5).then(res => setPopular(res.datasets)).catch(() => {})
  }, [])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">Loading dashboard...</p>
      </div>
    )
  }

  if (error || !summary) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md">
          {error || 'Failed to load dashboard'}
        </div>
      </div>
    )
  }

  const scoreBarColor = (score: number) => {
    if (score >= 85) return 'bg-green-500'
    if (score >= 70) return 'bg-green-400'
    if (score >= 50) return 'bg-orange-500'
    return 'bg-red-500'
  }

  // Score distribution chart max
  const maxBucket = Math.max(...Object.values(summary.score_distribution), 1)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Dataset readiness overview</p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Total Datasets</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{summary.total_datasets}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Average Score</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{summary.average_score}<span className="text-lg text-gray-500">/100</span></p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Production Ready</p>
          <p className="text-3xl font-bold text-green-600 mt-1">
            {(summary.status_distribution['production_ready'] || 0) + (summary.status_distribution['gold'] || 0)}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Needs Attention</p>
          <p className="text-3xl font-bold text-red-600 mt-1">
            {(summary.status_distribution['draft'] || 0)}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Score Distribution */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Score Distribution</h2>
          <div className="space-y-3">
            {Object.entries(summary.score_distribution).map(([bucket, count]) => (
              <div key={bucket} className="flex items-center gap-3">
                <span className="text-sm text-gray-600 w-16">{bucket}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-6 relative">
                  <div
                    className={`h-6 rounded-full ${
                      bucket === '85-100' ? 'bg-green-500' :
                      bucket === '70-84' ? 'bg-green-400' :
                      bucket === '50-69' ? 'bg-yellow-500' :
                      bucket === '25-49' ? 'bg-orange-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${(count / maxBucket) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-semibold text-gray-900 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Status Distribution */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Status Distribution</h2>
          <div className="space-y-3">
            {['gold', 'production_ready', 'internal', 'draft'].map((status) => {
              const count = summary.status_distribution[status] || 0
              const pct = summary.total_datasets > 0 ? (count / summary.total_datasets) * 100 : 0
              return (
                <div key={status} className="flex items-center gap-3">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full w-32 justify-center ${getStatusBadgeClass(status)}`}>
                    {getStatusLabel(status)}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-6">
                    <div
                      className={`h-6 rounded-full ${
                        status === 'gold' ? 'bg-yellow-400' :
                        status === 'production_ready' ? 'bg-green-500' :
                        status === 'internal' ? 'bg-blue-500' :
                        'bg-gray-400'
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-gray-900 w-8 text-right">{count}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Dimension Health */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Dimension Health</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {['ownership', 'documentation', 'schema_hygiene', 'data_quality', 'stability', 'operational'].map((dim) => {
            const pct = summary.dimension_health[dim] || 0
            return (
              <div key={dim} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-700">{getDimensionLabel(dim)}</span>
                  <span className="font-semibold text-gray-900">{pct}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${scoreBarColor(pct)}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Score Trend Sparkline */}
      {trends && trends.trends.length > 1 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Score Trend (Last {trends.days} Days)</h2>
          <div className="h-24 relative">
            <svg viewBox={`0 0 ${trends.trends.length * 20} 100`} className="w-full h-full" preserveAspectRatio="none">
              {(() => {
                const scores = trends.trends.map(t => t.avg_score)
                const minS = Math.min(...scores) - 5
                const maxS = Math.max(...scores) + 5
                const range = maxS - minS || 1
                const points = scores.map((s, i) =>
                  `${i * 20},${100 - ((s - minS) / range) * 80}`
                ).join(' ')
                return (
                  <>
                    <polyline
                      points={points}
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="2"
                      vectorEffect="non-scaling-stroke"
                    />
                    {scores.map((s, i) => (
                      <circle
                        key={i}
                        cx={i * 20}
                        cy={100 - ((s - minS) / range) * 80}
                        r="3"
                        fill="#3b82f6"
                      />
                    ))}
                  </>
                )
              })()}
            </svg>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{trends.trends[0]?.date}</span>
            <span>{trends.trends[trends.trends.length - 1]?.date}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Top Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Recommended Actions</h2>
          {summary.top_actions.length > 0 ? (
            <div className="space-y-3">
              {summary.top_actions.map((action) => (
                <div key={action.action_key} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{action.title}</p>
                    <p className="text-xs text-gray-500">{action.dataset_count} dataset{action.dataset_count !== 1 ? 's' : ''}</p>
                  </div>
                  <span className="text-sm font-semibold text-green-600">+{action.total_gain} pts</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 italic">No actions available</p>
          )}
        </div>

        {/* Needs Attention */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Needs Attention</h2>
          {summary.lowest_scoring.length > 0 ? (
            <div className="space-y-3">
              {summary.lowest_scoring.map((ds) => (
                <Link
                  key={ds.id}
                  href={`/datasets/${ds.id}`}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{ds.display_name}</p>
                    <p className="text-xs text-gray-500">{ds.full_name}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-gray-900">{ds.readiness_score}</span>
                    <span className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-full ${getStatusBadgeClass(ds.readiness_status)}`}>
                      {getStatusLabel(ds.readiness_status)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 italic">No datasets</p>
          )}
        </div>
      </div>

      {/* Recently Scored */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recently Scored</h2>
        {summary.recently_scored.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dataset</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Scored</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {summary.recently_scored.map((ds) => (
                  <tr key={ds.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link href={`/datasets/${ds.id}`} className="text-sm font-medium text-blue-600 hover:text-blue-800">
                        {ds.display_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm font-semibold text-gray-900">{ds.readiness_score}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-full ${getStatusBadgeClass(ds.readiness_status)}`}>
                        {getStatusLabel(ds.readiness_status)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {ds.last_scored_at ? new Date(ds.last_scored_at).toLocaleDateString() : 'Never'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-400 italic">No datasets scored yet</p>
        )}
      </div>

      {/* Most Popular */}
      {popular.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Most Viewed</h2>
          <div className="space-y-3">
            {popular.map((ds, i) => (
              <Link key={ds.id} href={`/datasets/${ds.id}`} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-gray-400 w-5">{i + 1}</span>
                  <div>
                    <div className="text-sm font-medium text-gray-900">{ds.display_name}</div>
                    <div className="text-xs text-gray-500">{ds.view_count} views · {ds.unique_viewers} viewers</div>
                  </div>
                </div>
                <span className="text-sm font-semibold text-gray-700">{ds.readiness_score}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
