'use client'

import Link from 'next/link'
import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism'
import { DatasetDetail, generateProtobufSchema, generateScalaSchema, generatePythonSchema } from '../../../api/client'

interface DatasetContentProps {
  dataset: DatasetDetail
  activeTab: 'overview' | 'score' | 'metadata' | 'schema'
  setActiveTab: (tab: 'overview' | 'score' | 'metadata' | 'schema') => void
  historyData: any[]
  maxScore: number
  minScore: number
  getStatusBadgeClass: (status: string) => string
  getStatusLabel: (status: string) => string
  getDimensionLabel: (key: string) => string
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

export default function DatasetContent(props: DatasetContentProps) {
  const {
    dataset,
    activeTab,
    setActiveTab,
    historyData,
    maxScore,
    minScore,
    getStatusBadgeClass,
    getStatusLabel,
    getDimensionLabel,
    isEditingOwner,
    isEditingMetadata,
    ownerName,
    ownerContact,
    intendedUse,
    limitations,
    displayName,
    setOwnerName,
    setOwnerContact,
    setIntendedUse,
    setLimitations,
    setDisplayName,
    setIsEditingOwner,
    setIsEditingMetadata,
    aiDescriptionSuggestion,
    loadingAiDescription,
    aiColumnSuggestions,
    applyingDescription,
    applyingColumns,
    setAiDescriptionSuggestion,
    setAiColumnSuggestions,
    handleUpdateOwner,
    handleUpdateMetadata,
    handleGenerateDescription,
    handleApplyDescription,
    handleGenerateColumnDescriptions,
    handleApplyColumnDescriptions,
  } = props

  // Schema generation state
  const [generatingSchema, setGeneratingSchema] = useState<string | null>(null)
  const [generatedSchema, setGeneratedSchema] = useState<{ format: string; schema: string; test_code: string; dataset_name: string } | null>(null)
  const [activeSubTab, setActiveSubTab] = useState<'schema' | 'tests'>('schema')
  
  // Score analysis - track which dimension dropdowns are open
  const [openDimensionDropdowns, setOpenDimensionDropdowns] = useState<Set<string>>(new Set())

  // Helper function to format location information
  const formatLocation = () => {
    if (!dataset.location_type || !dataset.location_data) {
      return null
    }

    const type = dataset.location_type.toLowerCase()
    const data = dataset.location_data

    switch (type) {
      case 's3':
        return {
          label: 'S3',
          display: data.bucket && data.key 
            ? `s3://${data.bucket}/${data.key}`
            : data.bucket && data.prefix
            ? `s3://${data.bucket}/${data.prefix}`
            : data.bucket
            ? `s3://${data.bucket}`
            : 'S3 Location',
          details: [
            { label: 'Bucket', value: data.bucket },
            { label: 'Key', value: data.key || data.prefix },
            { label: 'Region', value: data.region },
          ].filter(item => item.value),
        }
      case 'databricks':
        return {
          label: 'Databricks',
          display: [
            data.catalog,
            data.schema || data.database,
            data.table,
          ].filter(Boolean).join('.') || 'Databricks Location',
          details: [
            { label: 'Catalog', value: data.catalog },
            { label: 'Schema', value: data.schema || data.database },
            { label: 'Table', value: data.table },
          ].filter(item => item.value),
        }
      case 'snowflake':
        return {
          label: 'Snowflake',
          display: [
            data.database,
            data.schema,
            data.table,
          ].filter(Boolean).join('.') || 'Snowflake Location',
          details: [
            { label: 'Database', value: data.database },
            { label: 'Schema', value: data.schema },
            { label: 'Table', value: data.table },
            { label: 'Warehouse', value: data.warehouse },
          ].filter(item => item.value),
        }
      case 'bigquery':
        return {
          label: 'BigQuery',
          display: [
            data.project,
            data.dataset,
            data.table,
          ].filter(Boolean).join('.') || 'BigQuery Location',
          details: [
            { label: 'Project', value: data.project },
            { label: 'Dataset', value: data.dataset },
            { label: 'Table', value: data.table },
          ].filter(item => item.value),
        }
      default:
        return {
          label: type.charAt(0).toUpperCase() + type.slice(1),
          display: JSON.stringify(data),
          details: Object.entries(data).map(([key, value]) => ({
            label: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
            value: String(value),
          })),
        }
    }
  }

  const locationInfo = formatLocation()

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
            {locationInfo && (
              <p className="text-sm text-gray-500 mt-1 font-mono">
                {locationInfo.display}
              </p>
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
              { id: 'metadata', label: 'Metadata' },
              { id: 'schema', label: 'Schema' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
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
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Quick Stats */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Stats</h2>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500">Readiness Score</p>
                  <p className="text-3xl font-bold text-gray-900">{dataset.readiness_score}/100</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  <span
                    className={'inline-flex px-3 py-1 text-sm font-semibold rounded-full ' + getStatusBadgeClass(
                      dataset.readiness_status
                    )}
                  >
                    {getStatusLabel(dataset.readiness_status)}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Last Scored</p>
                  <p className="text-sm text-gray-900">
                    {dataset.last_scored_at
                      ? new Date(dataset.last_scored_at).toLocaleDateString()
                      : 'Never'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Columns</p>
                  <p className="text-sm text-gray-900">{dataset.columns.length} columns</p>
                </div>
              </div>
            </div>

            {/* Description */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Description</h2>
              {dataset.description ? (
                <p className="text-sm text-gray-700">{dataset.description}</p>
              ) : (
                <p className="text-sm text-gray-400 italic">No description available</p>
              )}
            </div>

            {/* Owner Info */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Owner</h2>
              <div className="space-y-2">
                <div>
                  <p className="text-sm text-gray-500">Name</p>
                  <p className="text-sm text-gray-900">
                    {dataset.owner_name || <span className="text-gray-400 italic">Not assigned</span>}
                  </p>
                </div>
                {dataset.owner_contact && (
                  <div>
                    <p className="text-sm text-gray-500">Contact</p>
                    <p className="text-sm text-gray-900">{dataset.owner_contact}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Intended Use & Limitations */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Usage</h2>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Intended Use</p>
                  <p className="text-sm text-gray-900 mt-1">
                    {dataset.intended_use || <span className="text-gray-400 italic">Not specified</span>}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Limitations</p>
                  <p className="text-sm text-gray-900 mt-1">
                    {dataset.limitations || <span className="text-gray-400 italic">None specified</span>}
                  </p>
                </div>
              </div>
            </div>

            {/* Location */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Location</h2>
              {locationInfo ? (
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-500">Type</p>
                    <p className="text-sm font-medium text-gray-900 mt-1">{locationInfo.label}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Path</p>
                    <p className="text-sm font-mono text-gray-900 mt-1 break-all">{locationInfo.display}</p>
                  </div>
                  {locationInfo.details.length > 0 && (
                    <div className="pt-2 border-t border-gray-200">
                      <p className="text-sm text-gray-500 mb-2">Details</p>
                      <div className="space-y-2">
                        {locationInfo.details.map((detail, idx) => (
                          <div key={idx} className="flex justify-between">
                            <span className="text-sm text-gray-600">{detail.label}:</span>
                            <span className="text-sm font-medium text-gray-900">{detail.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-gray-400 italic">No location information available</p>
              )}
            </div>
          </div>
        )}

        {/* Score Analysis Tab */}
        {activeTab === 'score' && (
          <div className="space-y-6">
            {/* Dimension Breakdown */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Dimension Breakdown
              </h2>
              <div className="space-y-4">
                {dataset.dimension_scores.map((dim) => {
                  const isOpen = openDimensionDropdowns.has(dim.dimension_key)
                  
                  // Map action_key to dimension_key for filtering actions
                  const actionKeyToDimension: Record<string, string> = {
                    assign_owner: "ownership",
                    add_owner_contact: "ownership",
                    add_description: "documentation",
                    document_columns: "documentation",
                    fix_naming: "schema_hygiene",
                    reduce_nullable_columns: "schema_hygiene",
                    remove_legacy_columns: "schema_hygiene",
                    add_quality_checks: "data_quality",
                    define_sla: "data_quality",
                    resolve_failures: "data_quality",
                    prevent_breaking_changes: "stability",
                    add_changelog: "stability",
                    maintain_compatibility: "stability",
                    define_intended_use: "operational",
                    document_limitations: "operational",
                  }
                  const dimensionActions = dataset.actions.filter(a => {
                    const actionDimension = actionKeyToDimension[a.action_key]
                    return actionDimension === dim.dimension_key
                  })
                  
                  const hasImprovements = dimensionActions.length > 0
                  
                  return (
                    <div key={dim.dimension_key} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm font-medium text-gray-700">
                          {getDimensionLabel(dim.dimension_key)}
                          {dim.measured === false && (
                            <span className="ml-2 text-xs text-amber-600 font-medium">
                              (Not measured yet)
                            </span>
                          )}
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">
                            {dim.measured === false ? (
                              <span className="text-gray-400 italic">N/A</span>
                            ) : (
                              `${dim.points_awarded}/${dim.max_points}`
                            )}
                          </span>
                          {dim.measured && hasImprovements && (
                            <button
                              onClick={() => {
                                const newSet = new Set(openDimensionDropdowns)
                                if (isOpen) {
                                  newSet.delete(dim.dimension_key)
                                } else {
                                  newSet.add(dim.dimension_key)
                                }
                                setOpenDimensionDropdowns(newSet)
                              }}
                              className="ml-2 text-xs text-blue-600 hover:text-blue-800 font-medium"
                            >
                              {isOpen ? 'Hide' : 'Show'} improvements
                            </button>
                          )}
                        </div>
                      </div>
                      {dim.measured === false ? (
                        <div className="w-full bg-gray-100 rounded-full h-2">
                          <div className="h-2 rounded-full bg-gray-300" style={{ width: '100%' }}></div>
                        </div>
                      ) : (
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={'h-2 rounded-full ' + (
                              dim.percentage >= 80
                                ? 'bg-green-600'
                                : dim.percentage >= 50
                                ? 'bg-yellow-600'
                                : 'bg-red-600'
                            )}
                            style={{ width: dim.percentage + '%' }}
                          ></div>
                        </div>
                      )}
                      
                      {/* Dropdown for improvements */}
                      {isOpen && dim.measured && hasImprovements && (
                        <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
                          {/* Actions (Improvements) */}
                          {dimensionActions.length > 0 && (
                            <div>
                              <h4 className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                                Recommended Actions
                              </h4>
                              <div className="space-y-2">
                                {dimensionActions.map((action) => (
                                  <div
                                    key={action.id}
                                    className="flex items-start space-x-3 p-2 bg-blue-50 rounded-md"
                                  >
                                    <span className="text-blue-600 font-semibold text-xs">+{action.points_gain}</span>
                                    <div className="flex-1">
                                      <p className="text-xs font-medium text-gray-900">{action.title}</p>
                                      {action.description && (
                                        <p className="text-xs text-gray-600 mt-0.5">{action.description}</p>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Reasons - only show for measured dimensions */}
            {dataset.reasons.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Why this score?
                </h2>
                <div className="space-y-3">
                  {dataset.reasons.map((reason) => {
                    // Get dimension score to check if measured
                    const dimScore = dataset.dimension_scores.find(
                      (d) => d.dimension_key === reason.dimension_key
                    )
                    // Only show reason if dimension is measured
                    if (dimScore && !dimScore.measured) {
                      return null
                    }
                    return (
                      <div
                        key={reason.id}
                        className="flex items-start space-x-3 p-3 bg-red-50 rounded-md"
                      >
                        <span className="text-red-600 font-semibold">-{reason.points_lost}</span>
                        <div className="flex-1">
                          <p className="text-sm text-gray-900">{reason.message}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {getDimensionLabel(reason.dimension_key)}
                          </p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Improvement Checklist - only show for measured dimensions */}
            {dataset.actions.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Improvement Checklist
                </h2>
                <div className="space-y-3">
                  {dataset.actions
                    .map((action) => {
                      // Map action_key to dimension_key (simplified - backend already filters)
                      // This is a fallback in case backend doesn't filter
                      const actionKeyToDimension: Record<string, string> = {
                        assign_owner: "ownership",
                        add_owner_contact: "ownership",
                        add_description: "documentation",
                        document_columns: "documentation",
                        fix_naming: "schema_hygiene",
                        reduce_nullable_columns: "schema_hygiene",
                        remove_legacy_columns: "schema_hygiene",
                        add_quality_checks: "data_quality",
                        define_sla: "data_quality",
                        resolve_failures: "data_quality",
                        prevent_breaking_changes: "stability",
                        add_changelog: "stability",
                        maintain_compatibility: "stability",
                        define_intended_use: "operational",
                        document_limitations: "operational",
                      }
                      const dimensionKey = actionKeyToDimension[action.action_key]
                      if (dimensionKey) {
                        const dimScore = dataset.dimension_scores.find(
                          (d) => d.dimension_key === dimensionKey
                        )
                        // Only show action if dimension is measured
                        if (dimScore && !dimScore.measured) {
                          return null
                        }
                      }
                      return (
                        <div
                          key={action.id}
                          className="flex items-start space-x-3 p-3 bg-blue-50 rounded-md"
                        >
                          <span className="text-blue-600 font-semibold">+{action.points_gain}</span>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">{action.title}</p>
                            <p className="text-xs text-gray-600 mt-1">{action.description}</p>
                          </div>
                        </div>
                      )
                    })
                    .filter(Boolean)}
                </div>
              </div>
            )}

            {/* Score History */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Score History</h2>
              {historyData.length > 0 ? (
                <>
                  <div className="h-64 flex items-end space-x-1">
                    {historyData.map((entry, idx) => {
                      const height = ((entry.readiness_score - minScore) / (maxScore - minScore || 1)) * 100
                      return (
                        <div
                          key={entry.id}
                          className="flex-1 bg-blue-600 rounded-t hover:bg-blue-700 transition cursor-pointer"
                          style={{ height: Math.max(height, 5) + '%' }}
                          title={entry.readiness_score + ' on ' + new Date(entry.recorded_at).toLocaleDateString()}
                        ></div>
                      )
                    })}
                  </div>
                  <div className="mt-4 flex justify-between text-xs text-gray-500">
                    <span>
                      {new Date(historyData[0].recorded_at).toLocaleDateString()}
                    </span>
                    <span>
                      {new Date(historyData[historyData.length - 1].recorded_at).toLocaleDateString()}
                    </span>
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p className="text-sm">No score history available</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Metadata Tab */}
        {activeTab === 'metadata' && (
          <div className="space-y-6">
            {/* Description Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Description</h2>
                {!isEditingMetadata && (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleGenerateDescription}
                      disabled={loadingAiDescription}
                      className="text-sm text-purple-600 hover:text-purple-800 disabled:text-gray-400"
                      title="Generate dataset description from table/column names"
                    >
                      {loadingAiDescription ? 'Generating...' : '✨ AI Suggest'}
                    </button>
                    <button
                      onClick={() => setIsEditingMetadata(true)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Edit
                    </button>
                  </div>
                )}
              </div>

              {/* AI Column Descriptions Suggestion */}
              {aiColumnSuggestions && Object.keys(aiColumnSuggestions).length > 0 && (
                <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
                  <div className="flex justify-between items-start mb-3">
                    <p className="text-sm font-medium text-blue-800">✨ AI Column Descriptions</p>
                    <button
                      onClick={() => setAiColumnSuggestions(null)}
                      className="text-blue-600 hover:text-blue-800 text-lg leading-none"
                    >
                      ×
                    </button>
                  </div>
                  
                  <div className="mb-3 space-y-2 max-h-64 overflow-y-auto">
                    {Object.entries(aiColumnSuggestions).map(([colName, description]) => (
                      <div key={colName} className="bg-white rounded border border-gray-200 p-2">
                        <div className="text-xs font-medium text-gray-700 mb-1">{colName}</div>
                        <div className="text-sm text-gray-900">{description}</div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={handleApplyColumnDescriptions}
                      disabled={applyingColumns}
                      className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                      {applyingColumns ? 'Applying...' : 'Apply All'}
                    </button>
                    <button
                      onClick={() => setAiColumnSuggestions(null)}
                      className="px-3 py-1.5 bg-white text-gray-700 text-sm rounded border border-gray-300 hover:bg-gray-50"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              )}

              {/* AI Description Suggestion with Diff Preview */}
              {aiDescriptionSuggestion && !isEditingMetadata && (
                <div className="mb-4 p-4 bg-purple-50 border border-purple-200 rounded-md">
                  <div className="flex justify-between items-start mb-3">
                    <p className="text-sm font-medium text-purple-800">✨ AI Suggestion</p>
                    <button
                      onClick={() => setAiDescriptionSuggestion(null)}
                      className="text-purple-600 hover:text-purple-800 text-lg leading-none"
                    >
                      ×
                    </button>
                  </div>
                  
                  {/* Diff Preview */}
                  <div className="mb-3 bg-white rounded border border-gray-200 p-3">
                    <div className="text-xs text-gray-500 mb-1">Current:</div>
                    <div className="text-sm text-gray-400 italic mb-3 min-h-[1.5rem]">
                      {dataset.description || <span className="text-gray-300">(No description)</span>}
                    </div>
                    <div className="text-xs text-gray-500 mb-1">Suggested:</div>
                    <div className="text-sm text-gray-900">
                      {aiDescriptionSuggestion}
                    </div>
                  </div>
                  
                  <div className="flex space-x-2">
                    <button
                      onClick={handleApplyDescription}
                      disabled={applyingDescription}
                      className="px-3 py-1.5 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                      {applyingDescription ? 'Applying...' : 'Apply'}
                    </button>
                    <button
                      onClick={() => setAiDescriptionSuggestion(null)}
                      className="px-3 py-1.5 bg-white text-gray-700 text-sm rounded border border-gray-300 hover:bg-gray-50"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              )}

              {/* Dataset Description Display */}
              {!isEditingMetadata && dataset.description && (
                <div className="mb-4 p-3 bg-gray-50 rounded-md">
                  <div className="text-xs font-medium text-gray-500 mb-1">Description</div>
                  <p className="text-sm text-gray-900">{dataset.description}</p>
                </div>
              )}

              {isEditingMetadata ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Display Name
                    </label>
                    <input
                      type="text"
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Intended Use
                    </label>
                    <textarea
                      value={intendedUse}
                      onChange={(e) => setIntendedUse(e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Limitations
                    </label>
                    <textarea
                      value={limitations}
                      onChange={(e) => setLimitations(e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={handleUpdateMetadata}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => {
                        setIsEditingMetadata(false)
                        setDisplayName(dataset.display_name)
                        setIntendedUse(dataset.intended_use || '')
                        setLimitations(dataset.limitations || '')
                      }}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-700">Intended Use</p>
                    <p className="text-sm text-gray-900 mt-1">
                      {dataset.intended_use || (
                        <span className="text-gray-400 italic">Not specified</span>
                      )}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700">Limitations</p>
                    <p className="text-sm text-gray-900 mt-1">
                      {dataset.limitations || (
                        <span className="text-gray-400 italic">None specified</span>
                      )}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Owner Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Owner</h2>
                {!isEditingOwner && (
                  <button
                    onClick={() => setIsEditingOwner(true)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Edit
                  </button>
                )}
              </div>

              {isEditingOwner ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Owner Name
                    </label>
                    <input
                      type="text"
                      value={ownerName}
                      onChange={(e) => setOwnerName(e.target.value)}
                      placeholder="e.g., Data Team"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Contact
                    </label>
                    <input
                      type="text"
                      value={ownerContact}
                      onChange={(e) => setOwnerContact(e.target.value)}
                      placeholder="e.g., #data-team or email@example.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={handleUpdateOwner}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={() => {
                        setIsEditingOwner(false)
                        setOwnerName(dataset.owner_name || '')
                        setOwnerContact(dataset.owner_contact || '')
                      }}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <div>
                    <p className="text-sm font-medium text-gray-700">Owner</p>
                    <p className="text-sm text-gray-900 mt-1">
                      {dataset.owner_name || (
                        <span className="text-gray-400 italic">No owner assigned</span>
                      )}
                    </p>
                  </div>
                  {dataset.owner_contact && (
                    <div>
                      <p className="text-sm font-medium text-gray-700">Contact</p>
                      <p className="text-sm text-gray-900 mt-1">{dataset.owner_contact}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Schema Tab */}
        {activeTab === 'schema' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Data Schema</h2>
                {dataset.columns && dataset.columns.length > 0 && (
                  <div className="flex space-x-2">
                    <button
                      onClick={async () => {
                        setGeneratingSchema('protobuf')
                        setGeneratedSchema(null)
                        try {
                          const result = await generateProtobufSchema(dataset.id)
                          setGeneratedSchema(result)
                        setActiveSubTab('schema')
                        } catch (err) {
                          alert(err instanceof Error ? err.message : 'Failed to generate protobuf schema')
                        } finally {
                          setGeneratingSchema(null)
                        }
                      }}
                      disabled={generatingSchema !== null}
                      className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                      {generatingSchema === 'protobuf' ? 'Generating...' : 'Generate Protobuf'}
                    </button>
                    <button
                      onClick={async () => {
                        setGeneratingSchema('scala')
                        setGeneratedSchema(null)
                        try {
                          const result = await generateScalaSchema(dataset.id)
                          setGeneratedSchema(result)
                        setActiveSubTab('schema')
                        } catch (err) {
                          alert(err instanceof Error ? err.message : 'Failed to generate Scala schema')
                        } finally {
                          setGeneratingSchema(null)
                        }
                      }}
                      disabled={generatingSchema !== null}
                      className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                      title="Generates Java classes (Scala-compatible)"
                    >
                      {generatingSchema === 'scala' ? 'Generating...' : 'Generate Java/Scala'}
                    </button>
                    <button
                      onClick={async () => {
                        setGeneratingSchema('python')
                        setGeneratedSchema(null)
                        try {
                          const result = await generatePythonSchema(dataset.id)
                          setGeneratedSchema(result)
                        setActiveSubTab('schema')
                        } catch (err) {
                          alert(err instanceof Error ? err.message : 'Failed to generate Python schema')
                        } finally {
                          setGeneratingSchema(null)
                        }
                      }}
                      disabled={generatingSchema !== null}
                      className="px-3 py-1.5 text-sm bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                      {generatingSchema === 'python' ? 'Generating...' : 'Generate Python'}
                    </button>
                  </div>
                )}
              </div>
              {dataset.columns && dataset.columns.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Column
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Nullable
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Description
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {dataset.columns.map((column) => (
                      <tr key={column.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {column.name}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="text-sm text-gray-600">
                            {column.type || (
                              <span className="text-gray-400 italic">Unknown</span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="text-sm text-gray-600">
                            {column.nullable === true ? (
                              <span className="text-orange-600">Yes</span>
                            ) : column.nullable === false ? (
                              <span className="text-green-600">No</span>
                            ) : (
                              <span className="text-gray-400 italic">Unknown</span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-sm text-gray-600">
                            {column.description || (
                              <span className="text-gray-400 italic">No description</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p className="text-sm">No schema information available</p>
                <p className="text-xs mt-1 text-gray-400">
                  Schema will be populated when dataset is ingested with column metadata
                </p>
              </div>
            )}
            </div>

            {/* Generated Schema Display */}
            {generatedSchema && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Generated {generatedSchema.format === 'scala' ? 'Java (Scala-compatible)' : generatedSchema.format.charAt(0).toUpperCase() + generatedSchema.format.slice(1)} Schema
                    </h3>
                    {generatedSchema.format === 'scala' && (
                      <p className="text-xs text-gray-500 mt-1">
                        Note: Avrotize generates Java classes which Scala can use directly
                      </p>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => {
                        const content = activeSubTab === 'schema' ? generatedSchema.schema : generatedSchema.test_code
                        const blob = new Blob([content], { type: 'text/plain' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        let extension: string
                        let filename: string
                        if (generatedSchema.format === 'protobuf') {
                          extension = 'proto'
                          filename = `${generatedSchema.dataset_name.replace(/\s+/g, '_')}.${extension}`
                        } else if (generatedSchema.format === 'scala') {
                          extension = 'java'
                          filename = `${generatedSchema.dataset_name.replace(/\s+/g, '_')}${activeSubTab === 'tests' ? '_Test' : ''}.${extension}`
                        } else if (generatedSchema.format === 'python') {
                          extension = 'py'
                          filename = `${generatedSchema.dataset_name.replace(/\s+/g, '_')}${activeSubTab === 'tests' ? '_test' : ''}.${extension}`
                        } else {
                          extension = generatedSchema.format
                          filename = `${generatedSchema.dataset_name.replace(/\s+/g, '_')}${activeSubTab === 'tests' ? '_test' : ''}.${extension}`
                        }
                        a.href = url
                        a.download = filename
                        document.body.appendChild(a)
                        a.click()
                        document.body.removeChild(a)
                        URL.revokeObjectURL(url)
                      }}
                      className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Download {activeSubTab === 'tests' ? 'Tests' : 'Schema'}
                    </button>
                    <button
                      onClick={() => setGeneratedSchema(null)}
                      className="px-3 py-1.5 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                    >
                      Close
                    </button>
                  </div>
                </div>

                {/* Subtabs for Schema and Tests */}
                {generatedSchema.test_code && (
                  <div className="mb-4 border-b border-gray-200">
                    <nav className="flex -mb-px" aria-label="Sub-tabs">
                      <button
                        onClick={() => setActiveSubTab('schema')}
                        className={
                          'px-4 py-2 text-sm font-medium border-b-2 transition-colors ' +
                          (activeSubTab === 'schema'
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300')
                        }
                      >
                        Schema
                      </button>
                      <button
                        onClick={() => setActiveSubTab('tests')}
                        className={
                          'px-4 py-2 text-sm font-medium border-b-2 transition-colors ' +
                          (activeSubTab === 'tests'
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300')
                        }
                      >
                        Tests
                      </button>
                    </nav>
                  </div>
                )}

                {/* Code Display */}
                <div className="rounded-md overflow-hidden border border-gray-200">
                  <SyntaxHighlighter
                    language={
                      generatedSchema.format === 'protobuf' ? 'protobuf' :
                      generatedSchema.format === 'scala' ? 'java' :
                      generatedSchema.format === 'python' ? 'python' :
                      'text'
                    }
                    style={vscDarkPlus}
                    customStyle={{
                      margin: 0,
                      borderRadius: '0.375rem',
                      fontSize: '0.875rem',
                      lineHeight: '1.5',
                      padding: '1rem',
                    }}
                    showLineNumbers={true}
                    wrapLines={true}
                    wrapLongLines={true}
                    PreTag="div"
                  >
                    {activeSubTab === 'schema' ? generatedSchema.schema : (generatedSchema.test_code || 'No test code generated')}
                  </SyntaxHighlighter>
                </div>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  )
}

