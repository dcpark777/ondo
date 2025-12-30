'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import {
  getDatasetDetail,
  updateOwner,
  updateMetadata,
  generateDatasetDescription,
  DatasetDetail,
  DatasetDescriptionRequest,
} from '../../api/client'

export default function DatasetDetailPage() {
  const params = useParams()
  const id = params.id as string

  const [dataset, setDataset] = useState<DatasetDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Edit state
  const [isEditingOwner, setIsEditingOwner] = useState(false)
  const [isEditingMetadata, setIsEditingMetadata] = useState(false)
  const [ownerName, setOwnerName] = useState('')
  const [ownerContact, setOwnerContact] = useState('')
  const [intendedUse, setIntendedUse] = useState('')
  const [limitations, setLimitations] = useState('')
  const [displayName, setDisplayName] = useState('')
  
  // AI assist state
  const [aiDescriptionSuggestion, setAiDescriptionSuggestion] = useState<string | null>(null)
  const [loadingAiDescription, setLoadingAiDescription] = useState(false)

  const fetchDataset = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getDatasetDetail(id)
      setDataset(data)
      setOwnerName(data.owner_name || '')
      setOwnerContact(data.owner_contact || '')
      setIntendedUse(data.intended_use || '')
      setLimitations(data.limitations || '')
      setDisplayName(data.display_name)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dataset')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      fetchDataset()
    }
  }, [id])

  const handleUpdateOwner = async () => {
    if (!dataset) return
    try {
      const updated = await updateOwner(id, {
        owner_name: ownerName || undefined,
        owner_contact: ownerContact || undefined,
      })
      // Refresh dataset data to get updated score, actions, and history
      setDataset(updated)
      setIsEditingOwner(false)
      // Optionally show success message
      // The UI will automatically update with new score, actions, and history
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update owner')
    }
  }

  const handleUpdateMetadata = async () => {
    if (!dataset) return
    try {
      const updated = await updateMetadata(id, {
        display_name: displayName || undefined,
        intended_use: intendedUse || undefined,
        limitations: limitations || undefined,
      })
      // Refresh dataset data to get updated score, actions, and history
      setDataset(updated)
      setIsEditingMetadata(false)
      // Optionally show success message
      // The UI will automatically update with new score, actions, and history
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update metadata')
    }
  }

  const handleGenerateDescription = async () => {
    if (!dataset) return
    setLoadingAiDescription(true)
    setAiDescriptionSuggestion(null)
    try {
      const request: DatasetDescriptionRequest = {
        full_name: dataset.full_name,
        display_name: dataset.display_name,
        owner_name: dataset.owner_name || undefined,
        intended_use: dataset.intended_use || undefined,
        limitations: dataset.limitations || undefined,
      }
      const response = await generateDatasetDescription(request)
      setAiDescriptionSuggestion(response.suggested_description)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to generate description'
      if (errorMsg.includes('not enabled')) {
        alert('AI assist is not enabled. Please enable it in backend configuration.')
      } else {
        alert(errorMsg)
      }
    } finally {
      setLoadingAiDescription(false)
    }
  }

  const handleApplyDescription = () => {
    if (aiDescriptionSuggestion) {
      // Note: We don't have a description field in the metadata form yet
      // For now, we'll show it in an alert and user can copy it
      navigator.clipboard.writeText(aiDescriptionSuggestion)
      alert('Description copied to clipboard! Paste it into your description field.')
    }
  }

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'gold':
        return 'bg-yellow-100 text-yellow-800'
      case 'production_ready':
        return 'bg-green-100 text-green-800'
      case 'internal':
        return 'bg-blue-100 text-blue-800'
      case 'draft':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'gold':
        return 'Gold'
      case 'production_ready':
        return 'Production Ready'
      case 'internal':
        return 'Internal'
      case 'draft':
        return 'Draft'
      default:
        return status
    }
  }

  const getDimensionLabel = (key: string) => {
    const labels: Record<string, string> = {
      ownership: 'Ownership & Accountability',
      documentation: 'Documentation Quality',
      schema_hygiene: 'Schema Hygiene',
      data_quality: 'Data Quality Signals',
      stability: 'Stability & Change Management',
      operational: 'Operational Metadata',
    }
    return labels[key] || key
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading dataset...</p>
        </div>
      </div>
    )
  }

  if (error || !dataset) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md">
          {error || 'Dataset not found'}
        </div>
        <a
          href="/datasets"
          className="mt-4 inline-block text-blue-600 hover:text-blue-800 underline"
        >
          ← Back to Datasets
        </a>
      </div>
    )
  }

  // Prepare score history for chart (last 30 entries, sorted by date)
  const historyData = [...dataset.score_history]
    .sort((a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime())
    .slice(-30)

  const maxScore = Math.max(...historyData.map((h) => h.readiness_score), 100)
  const minScore = Math.min(...historyData.map((h) => h.readiness_score), 0)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <Link
        href="/datasets"
        className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-6"
      >
        ← Back to Datasets
      </Link>

      {/* Score Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {dataset.display_name}
            </h1>
            <p className="text-gray-600">{dataset.full_name}</p>
          </div>
          <div className="text-right">
            <div className="text-5xl font-bold text-gray-900 mb-2">
              {dataset.readiness_score}
              <span className="text-2xl text-gray-500">/100</span>
            </div>
            <span
              className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusBadgeClass(
                dataset.readiness_status
              )}`}
            >
              {getStatusLabel(dataset.readiness_status)}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Dimension Breakdown */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Dimension Breakdown
            </h2>
            <div className="space-y-4">
              {dataset.dimension_scores.map((dim) => (
                <div key={dim.dimension_key}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-medium text-gray-700">
                      {getDimensionLabel(dim.dimension_key)}
                    </span>
                    <span className="text-sm text-gray-600">
                      {dim.points_awarded}/{dim.max_points}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        dim.percentage >= 80
                          ? 'bg-green-600'
                          : dim.percentage >= 50
                          ? 'bg-yellow-600'
                          : 'bg-red-600'
                      }`}
                      style={{ width: `${dim.percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Reasons */}
          {dataset.reasons.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Why this score?
              </h2>
              <div className="space-y-3">
                {dataset.reasons.map((reason) => (
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
                ))}
              </div>
            </div>
          )}

          {/* Improvement Checklist */}
          {dataset.actions.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Improvement Checklist
              </h2>
              <div className="space-y-3">
                {dataset.actions.map((action) => (
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
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Metadata Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Metadata</h2>
              {!isEditingMetadata && (
                <div className="flex space-x-2">
                  <button
                    onClick={handleGenerateDescription}
                    disabled={loadingAiDescription}
                    className="text-sm text-purple-600 hover:text-purple-800 disabled:text-gray-400"
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

            {/* AI Description Suggestion */}
            {aiDescriptionSuggestion && !isEditingMetadata && (
              <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded-md">
                <div className="flex justify-between items-start mb-2">
                  <p className="text-xs font-medium text-purple-800">AI Suggestion</p>
                  <button
                    onClick={() => setAiDescriptionSuggestion(null)}
                    className="text-purple-600 hover:text-purple-800"
                  >
                    ×
                  </button>
                </div>
                <p className="text-sm text-gray-900 mb-2">{aiDescriptionSuggestion}</p>
                <div className="flex space-x-2">
                  <button
                    onClick={handleApplyDescription}
                    className="text-xs px-2 py-1 bg-purple-600 text-white rounded hover:bg-purple-700"
                  >
                    Copy
                  </button>
                </div>
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

          {/* Score History Chart */}
          {historyData.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Score History
              </h2>
              <div className="h-48 flex items-end space-x-1">
                {historyData.map((entry, idx) => {
                  const height = ((entry.readiness_score - minScore) / (maxScore - minScore || 1)) * 100
                  return (
                    <div
                      key={entry.id}
                      className="flex-1 bg-blue-600 rounded-t hover:bg-blue-700 transition"
                      style={{ height: `${Math.max(height, 5)}%` }}
                      title={`${entry.readiness_score} on ${new Date(entry.recorded_at).toLocaleDateString()}`}
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
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
