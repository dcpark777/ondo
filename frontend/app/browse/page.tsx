'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { listDatasets, DatasetListItem } from '../api/client'
import { getStatusBadgeClass, getStatusLabel, getLocationLabel, getClassificationLabel } from '../lib/dataset-utils'

type GroupBy = 'domain' | 'classification' | 'location_type' | 'readiness_status'

function groupDatasets(datasets: DatasetListItem[], field: GroupBy): Record<string, DatasetListItem[]> {
  const groups: Record<string, DatasetListItem[]> = {}
  datasets.forEach(ds => {
    let key: string
    switch (field) {
      case 'domain':
        key = ds.domain || 'Ungrouped'
        break
      case 'classification':
        key = ds.classification ? getClassificationLabel(ds.classification) : 'Ungrouped'
        break
      case 'location_type':
        key = ds.location_type ? getLocationLabel(ds.location_type) : 'Ungrouped'
        break
      case 'readiness_status':
        key = getStatusLabel(ds.readiness_status)
        break
      default:
        key = 'Ungrouped'
    }
    if (!groups[key]) groups[key] = []
    groups[key].push(ds)
  })
  // Sort groups - put Ungrouped last
  const sorted: Record<string, DatasetListItem[]> = {}
  Object.keys(groups)
    .sort((a, b) => {
      if (a === 'Ungrouped') return 1
      if (b === 'Ungrouped') return -1
      return a.localeCompare(b)
    })
    .forEach(key => { sorted[key] = groups[key] })
  return sorted
}

export default function BrowsePage() {
  const [datasets, setDatasets] = useState<DatasetListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [groupBy, setGroupBy] = useState<GroupBy>('domain')
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())

  useEffect(() => {
    listDatasets()
      .then(res => {
        setDatasets(res.datasets)
        // Expand all groups by default
        const groups = groupDatasets(res.datasets, 'domain')
        setExpandedGroups(new Set(Object.keys(groups)))
      })
      .catch(err => console.error('Failed to load datasets:', err))
      .finally(() => setLoading(false))
  }, [])

  // When groupBy changes, re-expand all
  useEffect(() => {
    const groups = groupDatasets(datasets, groupBy)
    setExpandedGroups(new Set(Object.keys(groups)))
  }, [groupBy, datasets])

  const toggleGroup = (group: string) => {
    setExpandedGroups((prev: Set<string>) => {
      const next = new Set(prev)
      if (next.has(group)) next.delete(group)
      else next.add(group)
      return next
    })
  }

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'text-green-600'
    if (score >= 70) return 'text-green-500'
    if (score >= 50) return 'text-yellow-600'
    if (score >= 25) return 'text-orange-500'
    return 'text-red-500'
  }

  const grouped = groupDatasets(datasets, groupBy)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Browse Datasets</h1>
        <p className="text-gray-600">Explore datasets organized by category</p>
      </div>

      {/* Group By Selector */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700">Group by:</span>
          <div className="flex gap-2">
            {([
              { value: 'domain', label: 'Domain' },
              { value: 'classification', label: 'Classification' },
              { value: 'location_type', label: 'Location' },
              { value: 'readiness_status', label: 'Status' },
            ] as { value: GroupBy; label: string }[]).map(opt => (
              <button
                key={opt.value}
                onClick={() => setGroupBy(opt.value)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  groupBy === opt.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading datasets...</p>
        </div>
      ) : Object.keys(grouped).length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow-sm border border-gray-200">
          <p className="text-gray-500">No datasets found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {Object.entries(grouped).map(([group, items]) => (
            <div key={group} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <button
                onClick={() => toggleGroup(group)}
                className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${expandedGroups.has(group) ? 'rotate-90' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <h3 className="text-base font-semibold text-gray-900">{group}</h3>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                    {items.length}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span>Avg score: {Math.round(items.reduce((sum, d) => sum + d.readiness_score, 0) / items.length)}</span>
                </div>
              </button>
              {expandedGroups.has(group) && (
                <div className="border-t border-gray-200">
                  <div className="divide-y divide-gray-100">
                    {items
                      .sort((a, b) => b.readiness_score - a.readiness_score)
                      .map(ds => (
                        <Link
                          key={ds.id}
                          href={`/datasets/${ds.id}`}
                          className="block px-5 py-3 hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-gray-900 truncate">{ds.display_name}</span>
                                <span className={`inline-flex px-2 py-0.5 text-xs font-semibold rounded-full ${getStatusBadgeClass(ds.readiness_status)}`}>
                                  {getStatusLabel(ds.readiness_status)}
                                </span>
                              </div>
                              <div className="text-xs text-gray-500 truncate mt-0.5">{ds.full_name}</div>
                            </div>
                            <div className="flex items-center gap-4 ml-4">
                              {ds.owner_name && (
                                <span className="text-xs text-gray-500">{ds.owner_name}</span>
                              )}
                              <div className="flex items-center gap-1">
                                <span className={`text-sm font-bold ${getScoreColor(ds.readiness_score)}`}>
                                  {ds.readiness_score}
                                </span>
                                <div className="w-16 bg-gray-200 rounded-full h-1.5">
                                  <div
                                    className={`h-1.5 rounded-full ${
                                      ds.readiness_score >= 85 ? 'bg-green-500' :
                                      ds.readiness_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                                    }`}
                                    style={{ width: `${ds.readiness_score}%` }}
                                  />
                                </div>
                              </div>
                            </div>
                          </div>
                        </Link>
                      ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
