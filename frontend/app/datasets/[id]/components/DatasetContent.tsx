'use client'

import Link from 'next/link'
import { DatasetDetail, ScoreHistory } from '../../../api/client'
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

interface DatasetContentProps {
  dataset: DatasetDetail
  activeTab: 'overview' | 'score' | 'schema' | 'lineage' | 'details'
  setActiveTab: (tab: 'overview' | 'score' | 'schema' | 'lineage' | 'details') => void
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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <Link
        href="/datasets"
        className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-6"
      >
        ← Back to Datasets
      </Link>

      {/* Header with Score */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {dataset.display_name}
            </h1>
            <p className="text-gray-600">{dataset.full_name}</p>
            {locationDisplay && (
              <div className="mt-2 flex items-center gap-2">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${getLocationBadgeColor(dataset.location_type)}`}>
                  {getLocationIcon(dataset.location_type)}
                  <span>{getLocationLabel(dataset.location_type)}</span>
                </span>
                <span className="text-sm text-gray-500 font-mono">
                  {locationDisplay}
                </span>
              </div>
            )}
          </div>
          <div className="text-right">
            <div className="text-5xl font-bold text-gray-900 mb-2">
              {dataset.readiness_score}
              <span className="text-2xl text-gray-500">/100</span>
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
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px" aria-label="Tabs">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'score', label: 'Score Analysis' },
              { id: 'schema', label: 'Schema' },
              { id: 'lineage', label: 'Lineage' },
              { id: 'details', label: 'Details' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'overview' | 'score' | 'schema' | 'lineage' | 'details')}
                className={
                  'px-6 py-4 text-sm font-medium border-b-2 transition-colors ' +
                  (activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300')
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
        {activeTab === 'details' && (
          <DetailsTab dataset={dataset} />
        )}
      </div>
    </div>
  )
}
