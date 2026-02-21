'use client'

import { useEffect, useState } from 'react'
import { DatasetDetail, AuditLogEntry, getDatasetAuditLog } from '../../../api/client'

interface ActivityTabProps {
  dataset: DatasetDetail
}

function getActionIcon(action: string): JSX.Element {
  switch (action) {
    case 'dataset.scored':
      return (
        <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    case 'owner.updated':
      return (
        <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    case 'metadata.updated':
      return (
        <svg className="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      )
    case 'tag.added':
    case 'tag.removed':
      return (
        <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
        </svg>
      )
    case 'quality_rule.created':
    case 'quality_rule.executed':
      return (
        <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    case 'description.generated':
      return (
        <svg className="w-5 h-5 text-pink-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      )
    default:
      return (
        <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
  }
}

function getActionDescription(entry: AuditLogEntry): string {
  const details = entry.details

  switch (entry.action) {
    case 'dataset.scored': {
      if (details && details.old_score !== undefined && details.new_score !== undefined) {
        const diff = details.new_score - details.old_score
        if (diff > 0) return `Score increased from ${details.old_score} to ${details.new_score} (+${diff})`
        if (diff < 0) return `Score decreased from ${details.old_score} to ${details.new_score} (${diff})`
        return `Dataset re-scored at ${details.new_score}`
      }
      return 'Dataset scored'
    }
    case 'owner.updated': {
      if (details?.new_owner_name) {
        return `Owner changed to ${details.new_owner_name}`
      }
      return 'Owner information updated'
    }
    case 'metadata.updated': {
      const changes: string[] = []
      if (details?.new_display_name && details.new_display_name !== details.old_display_name) {
        changes.push('display name')
      }
      if (details?.new_intended_use !== details?.old_intended_use) {
        changes.push('intended use')
      }
      if (details?.new_limitations !== details?.old_limitations) {
        changes.push('limitations')
      }
      if (changes.length > 0) {
        return `Updated ${changes.join(', ')}`
      }
      return 'Metadata updated'
    }
    case 'tag.added':
      return details?.tag ? `Tag "${details.tag}" added` : 'Tag added'
    case 'tag.removed':
      return details?.tag ? `Tag "${details.tag}" removed` : 'Tag removed'
    case 'quality_rule.created':
      return details?.rule_name ? `Quality rule "${details.rule_name}" created` : 'Quality rule created'
    case 'quality_rule.executed':
      return details?.rule_name ? `Quality rule "${details.rule_name}" executed` : 'Quality rule executed'
    case 'description.generated':
      return 'AI-generated description applied'
    case 'schema.snapshot':
      return 'Schema snapshot recorded'
    default:
      return entry.action.replace(/\./g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  }
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffSeconds < 60) return 'just now'
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  })
}

export default function ActivityTab({ dataset }: ActivityTabProps) {
  const [entries, setEntries] = useState<AuditLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getDatasetAuditLog(dataset.id, 100)
      .then((response) => {
        setEntries(response.entries)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load activity')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [dataset.id])

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-sm text-gray-500">Loading activity...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md text-sm">
          {error}
        </div>
      </div>
    )
  }

  if (entries.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="mt-3 text-sm font-medium text-gray-900">No activity yet</p>
          <p className="mt-1 text-sm text-gray-500">
            Activity will appear here as changes are made to this dataset.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Activity Timeline</h3>
        <p className="text-sm text-gray-500 mt-1">
          {entries.length} event{entries.length !== 1 ? 's' : ''} recorded
        </p>
      </div>

      <div className="px-6 py-4">
        <div className="flow-root">
          <ul className="-mb-8">
            {entries.map((entry, idx) => (
              <li key={entry.id}>
                <div className="relative pb-8">
                  {/* Connector line */}
                  {idx < entries.length - 1 && (
                    <span
                      className="absolute left-[10px] top-8 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  )}

                  <div className="relative flex items-start space-x-3">
                    {/* Icon */}
                    <div className="flex-shrink-0">
                      <div className="h-6 w-6 flex items-center justify-center">
                        {getActionIcon(entry.action)}
                      </div>
                    </div>

                    {/* Content */}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm text-gray-900">
                          {getActionDescription(entry)}
                        </p>
                        <span className="text-xs text-gray-500 whitespace-nowrap ml-4">
                          {formatRelativeTime(entry.created_at)}
                        </span>
                      </div>
                      {entry.actor && (
                        <p className="mt-0.5 text-xs text-gray-500">
                          by {entry.actor}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
