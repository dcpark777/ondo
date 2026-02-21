'use client'

import { useState, useEffect } from 'react'
import { DatasetDetail, getViewStats, ViewStats } from '../../../api/client'

interface UsageTabProps {
  dataset: DatasetDetail
}

export default function UsageTab({ dataset }: UsageTabProps) {
  const [stats, setStats] = useState<ViewStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  useEffect(() => {
    setLoading(true)
    getViewStats(dataset.id, days)
      .then(setStats)
      .catch(err => console.error('Failed to load usage stats:', err))
      .finally(() => setLoading(false))
  }, [dataset.id, days])

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">Loading usage data...</p>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>Failed to load usage statistics</p>
      </div>
    )
  }

  const maxDailyCount = Math.max(...(stats.daily_views.map(d => d.count)), 1)

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Period:</span>
        {[7, 30, 90].map(d => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={`px-3 py-1 rounded-md text-sm font-medium ${
              days === d ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {d}d
          </button>
        ))}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="text-sm font-medium text-gray-500 mb-1">Total Views</div>
          <div className="text-3xl font-bold text-gray-900">{stats.total_views}</div>
          <div className="text-xs text-gray-400 mt-1">Last {days} days</div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="text-sm font-medium text-gray-500 mb-1">Unique Viewers</div>
          <div className="text-3xl font-bold text-gray-900">{stats.unique_viewers}</div>
          <div className="text-xs text-gray-400 mt-1">Last {days} days</div>
        </div>
      </div>

      {/* Daily Views Chart */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Views</h3>
        {stats.daily_views.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No views recorded in this period</p>
        ) : (
          <div className="space-y-2">
            {stats.daily_views.map((day) => (
              <div key={day.date} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-20 text-right shrink-0">
                  {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </span>
                <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                  <div
                    className="bg-blue-500 h-5 rounded-full transition-all"
                    style={{ width: `${(day.count / maxDailyCount) * 100}%`, minWidth: day.count > 0 ? '8px' : '0' }}
                  />
                </div>
                <span className="text-xs font-medium text-gray-700 w-8">{day.count}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Viewers */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Viewers</h3>
        {stats.recent_viewers.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No viewers in this period</p>
        ) : (
          <div className="divide-y divide-gray-100">
            {stats.recent_viewers.map((viewer) => (
              <div key={viewer.user_id} className="flex items-center justify-between py-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                    <span className="text-xs font-medium text-gray-600">
                      {viewer.user_id.slice(0, 2).toUpperCase()}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{viewer.user_id}</span>
                </div>
                <span className="text-xs text-gray-500">
                  {new Date(viewer.last_viewed).toLocaleDateString('en-US', {
                    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                  })}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
