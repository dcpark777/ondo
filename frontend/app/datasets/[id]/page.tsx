'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  getDatasetDetail,
  updateOwner,
  updateMetadata,
  generateDatasetDescription,
  generateColumnDescriptions,
  applyDatasetDescription,
  applyColumnDescriptions,
  DatasetDetail,
  DatasetDescriptionRequest,
  ScoreHistory,
} from '../../api/client'
import DatasetContent from './components/DatasetContent'

export default function DatasetDetailPage() {
  const params = useParams()
  const router = useRouter()
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
  const [aiColumnSuggestions, setAiColumnSuggestions] = useState<Record<string, string> | null>(null)
  const [loadingAiColumns, setLoadingAiColumns] = useState(false)
  const [applyingDescription, setApplyingDescription] = useState(false)
  const [applyingColumns, setApplyingColumns] = useState(false)

  // Tab state - read from URL on mount
  const validTabs: Array<'overview' | 'score' | 'schema' | 'lineage' | 'details'> = ['overview', 'score', 'schema', 'lineage', 'details']
  
  // Get initial tab from URL
  const getTabFromUrl = (): 'overview' | 'score' | 'schema' | 'lineage' | 'details' => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const tab = params.get('tab')
      if (tab && validTabs.includes(tab as any)) {
        return tab as 'overview' | 'score' | 'schema' | 'lineage' | 'details'
      }
    }
    return 'overview'
  }

  const [activeTab, setActiveTab] = useState<'overview' | 'score' | 'schema' | 'lineage' | 'details'>(getTabFromUrl())

  // Update URL when tab changes
  const handleTabChange = (tab: 'overview' | 'score' | 'schema' | 'lineage' | 'details') => {
    setActiveTab(tab)
    const params = new URLSearchParams(window.location.search)
    if (tab === 'overview') {
      params.delete('tab') // Remove tab param for default tab
    } else {
      params.set('tab', tab)
    }
    const newUrl = `/datasets/${id}${params.toString() ? `?${params.toString()}` : ''}`
    router.push(newUrl, { scroll: false })
  }

  // Sync tab state with URL on mount and when URL changes
  useEffect(() => {
    // Check URL on mount
    const tab = getTabFromUrl()
    setActiveTab(tab)
    
    // Listen for browser back/forward
    const handlePopState = () => {
      const tab = getTabFromUrl()
      setActiveTab(tab)
    }
    
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [id]) // Re-check when dataset ID changes

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      // Extract column names from dataset name patterns for MVP
      // In a real system, we'd get this from the dataset detail response
      // For now, we'll infer common patterns from the dataset name
      const columnNames: string[] = [] // Placeholder - would come from dataset.columns
      
      const request: DatasetDescriptionRequest = {
        full_name: dataset.full_name,
        display_name: dataset.display_name,
        owner_name: dataset.owner_name || undefined,
        intended_use: dataset.intended_use || undefined,
        limitations: dataset.limitations || undefined,
        column_names: columnNames.length > 0 ? columnNames : undefined,
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

  const handleApplyDescription = async () => {
    if (!dataset || !aiDescriptionSuggestion) return
    setApplyingDescription(true)
    try {
      const updated = await applyDatasetDescription({
        dataset_id: dataset.id,
        description: aiDescriptionSuggestion,
      })
      setDataset(updated)
      setAiDescriptionSuggestion(null)
      // Show success message
      alert('Description applied! Dataset has been re-scored.')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to apply description')
    } finally {
      setApplyingDescription(false)
    }
  }

  const handleGenerateColumnDescriptions = async () => {
    if (!dataset) return
    setLoadingAiColumns(true)
    setAiColumnSuggestions(null)
    try {
      // Get undocumented columns - for MVP, we'll use a placeholder
      // In a real system, we'd get this from the dataset detail response
      const columnNames: string[] = [] // Placeholder - would come from dataset.columns
      
      if (columnNames.length === 0) {
        alert('No undocumented columns found. All columns already have descriptions.')
        return
      }

      const existingDescriptions: Record<string, string> = {} // Would come from dataset
      
      const response = await generateColumnDescriptions({
        dataset_name: dataset.display_name,
        column_names: columnNames,
        existing_descriptions: existingDescriptions,
      })
      setAiColumnSuggestions(response.suggested_descriptions)
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to generate column descriptions'
      if (errorMsg.includes('not enabled')) {
        alert('AI assist is not enabled. Please enable it in backend configuration.')
      } else {
        alert(errorMsg)
      }
    } finally {
      setLoadingAiColumns(false)
    }
  }

  const handleApplyColumnDescriptions = async () => {
    if (!dataset || !aiColumnSuggestions) return
    setApplyingColumns(true)
    try {
      const updated = await applyColumnDescriptions({
        dataset_id: dataset.id,
        column_descriptions: aiColumnSuggestions,
      })
      setDataset(updated)
      setAiColumnSuggestions(null)
      alert('Column descriptions applied! Dataset has been re-scored.')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to apply column descriptions')
    } finally {
      setApplyingColumns(false)
    }
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
  const scoreHistory = dataset.score_history;
  const historyData: ScoreHistory[] = scoreHistory ? scoreHistory.slice(-30) : [];
  const maxScore = 100;
  const minScore = 0;

  return (
    <DatasetContent
      dataset={dataset}
      activeTab={activeTab}
      setActiveTab={handleTabChange}
      historyData={historyData}
      maxScore={maxScore}
      minScore={minScore}
      isEditingOwner={isEditingOwner}
      isEditingMetadata={isEditingMetadata}
      ownerName={ownerName}
      ownerContact={ownerContact}
      intendedUse={intendedUse}
      limitations={limitations}
      displayName={displayName}
      setOwnerName={setOwnerName}
      setOwnerContact={setOwnerContact}
      setIntendedUse={setIntendedUse}
      setLimitations={setLimitations}
      setDisplayName={setDisplayName}
      setIsEditingOwner={setIsEditingOwner}
      setIsEditingMetadata={setIsEditingMetadata}
      aiDescriptionSuggestion={aiDescriptionSuggestion}
      loadingAiDescription={loadingAiDescription}
      aiColumnSuggestions={aiColumnSuggestions}
      applyingDescription={applyingDescription}
      applyingColumns={applyingColumns}
      setAiDescriptionSuggestion={setAiDescriptionSuggestion}
      setAiColumnSuggestions={setAiColumnSuggestions}
      handleUpdateOwner={handleUpdateOwner}
      handleUpdateMetadata={handleUpdateMetadata}
      handleGenerateDescription={handleGenerateDescription}
      handleApplyDescription={handleApplyDescription}
      handleGenerateColumnDescriptions={handleGenerateColumnDescriptions}
      handleApplyColumnDescriptions={handleApplyColumnDescriptions}
    />
  )
}
