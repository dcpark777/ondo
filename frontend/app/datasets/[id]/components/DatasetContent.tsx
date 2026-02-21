'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { DatasetDetail, ScoreHistory, checkWatch, startWatching, stopWatching, recordDatasetView, exportDataset } from '../../../api/client'
import {
  getStatusBadgeClass,
  getStatusLabel,
  getLocationIcon,
  getLocationLabel,
  getLocationBadgeColor,
} from '../../../lib/dataset-utils'
import OverviewTab from './OverviewTab'
import ScoreAnalysisTab from './ScoreAnalysisTab'
import SchemaTab from './SchemaTab'
import LineageTab from './LineageTab'
import DetailsTab from './DetailsTab'
import QualityTab from './QualityTab'
import UsageTab from './UsageTab'
import ActivityTab from './ActivityTab'

interface DatasetContentProps {
  dataset: DatasetDetail
  activeTab: 'overview' | 'score' | 'schema' | 'lineage' | 'quality' | 'usage' | 'activity' | 'details'
  setActiveTab: (tab: 'overview' | 'score' | 'schema' | 'lineage' | 'quality' | 'usage' | 'activity' | 'details') => void
  historyData: ScoreHistory[]
  maxScore: number
  minScore: number
  // Edit state
  isEditingOwner: boolean
  isEditingMetadata: boolean
  ownerName: string
  ownerContact: string
  intendedUse: string
  limitations: string
  displayName: string
  setOwnerName: (name: string) => void
  setOwnerContact: (contact: string) => void
  setIntendedUse: (use: string) => void
  setLimitations: (limitations: string) => void
  setDisplayName: (name: string) => void
  setIsEditingOwner: (editing: boolean) => void
  setIsEditingMetadata: (editing: boolean) => void
  // AI assist state
  aiDescriptionSuggestion: string | null
  loadingAiDescription: boolean
  aiColumnSuggestions: Record<string, string> | null
  applyingDescription: boolean
  applyingColumns: boolean
  setAiDescriptionSuggestion: (suggestion: string | null) => void
  setAiColumnSuggestions: (suggestions: Record<string, string> | null) => void
  // Handlers
  handleUpdateOwner: () => void
  handleUpdateMetadata: () => void
  handleGenerateDescription: () => void
  handleApplyDescription: () => void
  handleGenerateColumnDescriptions: () => void
  handleApplyColumnDescriptions: () => void
}

// Helper function to format location for the header
function formatLocationDisplay(dataset: DatasetDetail) {
  if (!dataset.location_type || !dataset.location_data) return null

  const type = dataset.location_type.toLowerCase()
  const data = dataset.location_data

  switch (type) {
    case 's3':
      return data.bucket && data.key
        ? `s3://${data.bucket}/${data.key}`
        : data.bucket && data.prefix
        ? `s3://${data.bucket}/${data.prefix}`
        : data.bucket
        ? `s3://${data.bucket}`
        : 'S3 Location'
    case 'databricks':
      return [data.catalog, data.schema || data.database, data.table].filter(Boolean).join('.') || 'Databricks Location'
    case 'snowflake':
      return [data.database, data.schema, data.table].filter(Boolean).join('.') || 'Snowflake Location'
    case 'bigquery':
      return [data.project, data.dataset, data.table].filter(Boolean).join('.') || 'BigQuery Location'
    case 'hive':
      return [data.database, data.table].filter(Boolean).join('.') || 'Hive Location'
    default:
      return JSON.stringify(data)
  }
}

function getUserId(): string {
  if (typeof window === 'undefined') return 'anonymous'
  let userId = localStorage.getItem('ondo_user_id')
  if (!userId) {
    userId = 'user_' + Math.random().toString(36).substring(2, 10)
    localStorage.setItem('ondo_user_id', userId)
  }
  return userId
}

export default function DatasetContent(props: DatasetContentProps) {
  const {
    dataset,
    activeTab,
    setActiveTab,
    historyData,
    maxScore,
    minScore,
    ...editAndAiProps
  } = props

  const locationDisplay = formatLocationDisplay(dataset)
  const [watching, setWatching] = useState(false)
  const [watchLoading, setWatchLoading] = useState(false)
  const [exportDropdownOpen, setExportDropdownOpen] = useState(false)
  const exportDropdownRef = useRef<HTMLDivElement>(null)

  // Close export dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (exportDropdownRef.current && !exportDropdownRef.current.contains(event.target as Node)) {
        setExportDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    const userId = getUserId()
    checkWatch(dataset.id, userId)
      .then((res) => setWatching(res.watching))
      .catch(() => {})
  }, [dataset.id])

  // Record dataset view
  useEffect(() => {
    const userId = getUserId()
    recordDatasetView(dataset.id, userId).catch(() => {})
  }, [dataset.id])

  const toggleWatch = async () => {
    setWatchLoading(true)
    try {
      const userId = getUserId()
      if (watching) {
        await stopWatching(dataset.id, userId)
        setWatching(false)
      } else {
        await startWatching(dataset.id, userId)
        setWatching(true)
      }
    } catch {
      // ignore
    } finally {
      setWatchLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <Link
        href="/datasets"
        className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 mb-6"
      >
        ← Back to Datasets
      </Link>

      {/* Header with Score */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="min-w-0">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2 truncate">
              {dataset.display_name}
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-sm sm:text-base truncate">{dataset.full_name}</p>
            {locationDisplay && (
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${getLocationBadgeColor(dataset.location_type)}`}>
                  {getLocationIcon(dataset.location_type)}
                  <span>{getLocationLabel(dataset.location_type)}</span>
                </span>
                <span className="text-sm text-gray-500 font-mono truncate">
                  {locationDisplay}
                </span>
              </div>
            )}
          </div>
          <div className="flex flex-row md:flex-col items-center md:items-end gap-3 md:gap-0">
            <div className="flex items-center gap-3 md:mb-2">
              <div className="relative" ref={exportDropdownRef}>
                <button
                  onClick={() => setExportDropdownOpen(!exportDropdownOpen)}
                  className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md border border-gray-300 bg-gray-50 text-gray-600 hover:bg-gray-100 transition-colors"
                  title="Export dataset"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Export
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {exportDropdownOpen && (
                  <div className="absolute right-0 mt-1 w-40 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 z-20">
                    <button
                      onClick={() => {
                        exportDataset(dataset.id, 'csv')
                        setExportDropdownOpen(false)
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-t-md"
                    >
                      Export CSV
                    </button>
                    <button
                      onClick={() => {
                        exportDataset(dataset.id, 'json')
                        setExportDropdownOpen(false)
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-b-md"
                    >
                      Export JSON
                    </button>
                  </div>
                )}
              </div>
              <button
                onClick={toggleWatch}
                disabled={watchLoading}
                className={
                  'inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md border transition-colors ' +
                  (watching
                    ? 'bg-yellow-50 border-yellow-300 text-yellow-700 hover:bg-yellow-100'
                    : 'bg-gray-50 border-gray-300 text-gray-600 hover:bg-gray-100')
                }
                title={watching ? 'Stop watching' : 'Watch for changes'}
              >
                <svg className="w-3.5 h-3.5" fill={watching ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                {watching ? 'Watching' : 'Watch'}
              </button>
              <div className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-gray-100">
                {dataset.readiness_score}
                <span className="text-xl sm:text-2xl text-gray-500">/100</span>
              </div>
            </div>
            <span
              className={'inline-flex px-3 py-1 text-sm font-semibold rounded-full ' + getStatusBadgeClass(
                dataset.readiness_status
              )}
            >
              {getStatusLabel(dataset.readiness_status)}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 mb-6">
        <div className="border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
          <nav className="flex -mb-px min-w-max" aria-label="Tabs">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'score', label: 'Score Analysis' },
              { id: 'schema', label: 'Schema' },
              { id: 'lineage', label: 'Lineage' },
              { id: 'quality', label: 'Quality Rules' },
              { id: 'usage', label: 'Usage' },
              { id: 'activity', label: 'Activity' },
              { id: 'details', label: 'Details' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'overview' | 'score' | 'schema' | 'lineage' | 'quality' | 'usage' | 'activity' | 'details')}
                className={
                  'px-6 py-4 text-sm font-medium border-b-2 transition-colors ' +
                  (activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:border-gray-600')
                }
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'overview' && (
          <OverviewTab dataset={dataset} {...editAndAiProps} />
        )}
        {activeTab === 'score' && (
          <ScoreAnalysisTab
            dataset={dataset}
            historyData={historyData}
            maxScore={maxScore}
            minScore={minScore}
          />
        )}
        {activeTab === 'schema' && (
          <SchemaTab dataset={dataset} />
        )}
        {activeTab === 'lineage' && (
          <LineageTab dataset={dataset} />
        )}
        {activeTab === 'quality' && (
          <QualityTab dataset={dataset} />
        )}
        {activeTab === 'usage' && (
          <UsageTab dataset={dataset} />
        )}
        {activeTab === 'activity' && (
          <ActivityTab dataset={dataset} />
        )}
        {activeTab === 'details' && (
          <DetailsTab dataset={dataset} />
        )}
      </div>
    </div>
  )
}
