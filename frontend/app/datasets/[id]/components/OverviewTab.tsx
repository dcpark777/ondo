'use client'

import { DatasetDetail } from '../../../api/client'
import {
  getStatusBadgeClass,
  getStatusLabel,
  getLocationIcon,
  getLocationLabel,
  getLocationBadgeColor,
  formatDataSize,
  formatSLA,
} from '../../../lib/dataset-utils'

interface OverviewTabProps {
  dataset: DatasetDetail
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

export default function OverviewTab(props: OverviewTabProps) {
  const {
    dataset,
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

  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Stats</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-500">Readiness Score</p>
            <p className="text-3xl font-bold text-gray-900">{dataset.readiness_score}/100</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <span
              className={'inline-flex px-3 py-1 text-sm font-semibold rounded-full mt-1 ' + getStatusBadgeClass(
                dataset.readiness_status
              )}
            >
              {getStatusLabel(dataset.readiness_status)}
            </span>
          </div>
          <div>
            <p className="text-sm text-gray-500">Columns</p>
            <p className="text-sm text-gray-900 mt-1">{dataset.columns.length} columns</p>
          </div>
        </div>
      </div>

      {/* Dataset Metadata */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Dataset Size & Files */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Dataset Size</h2>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-500">Data Size</p>
              <p className="text-sm font-medium text-gray-900 mt-1">
                {formatDataSize(dataset.data_size_bytes)}
              </p>
            </div>
            {dataset.file_count !== null && (
              <div>
                <p className="text-sm text-gray-500">Number of Files</p>
                <p className="text-sm font-medium text-gray-900 mt-1">
                  {dataset.file_count.toLocaleString()} {dataset.file_count === 1 ? 'file' : 'files'}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Partition Keys */}
        {dataset.partition_keys && dataset.partition_keys.length > 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Partition Keys</h2>
            <div className="flex flex-wrap gap-2">
              {dataset.partition_keys.map((key, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800"
                >
                  {key}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Partition Keys</h2>
            <p className="text-sm text-gray-400">No partition keys</p>
          </div>
        )}

        {/* SLA */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">SLA</h2>
          <div>
            <p className="text-sm text-gray-500">Update Frequency</p>
            <p className="text-sm font-medium text-gray-900 mt-1">
              {formatSLA(dataset.sla_hours)}
            </p>
          </div>
        </div>
      </div>

      {/* Producing Job */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Producing Job</h2>
        <div>
          <p className="text-sm text-gray-500">Job/Pipeline</p>
          <p className="text-sm font-medium text-gray-900 mt-1 font-mono">
            {dataset.producing_job || <span className="text-gray-400 italic">Not specified</span>}
          </p>
        </div>
      </div>

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
            {!dataset.description && (
              <p className="text-sm text-gray-400 italic">No description available</p>
            )}
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
  )
}
