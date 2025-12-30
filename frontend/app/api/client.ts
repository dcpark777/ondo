/**
 * API client utilities for backend communication
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface DatasetListItem {
  id: string
  full_name: string
  display_name: string
  owner_name: string | null
  readiness_score: number
  readiness_status: string
  last_scored_at: string | null
}

export interface DatasetListResponse {
  datasets: DatasetListItem[]
  total: number
}

export interface ListDatasetsParams {
  status?: string
  owner?: string
  q?: string
}

export interface DimensionScore {
  dimension_key: string
  points_awarded: number
  max_points: number
  percentage: number
}

export interface Reason {
  id: string
  dimension_key: string
  reason_code: string
  message: string
  points_lost: number
}

export interface Action {
  id: string
  action_key: string
  title: string
  description: string
  points_gain: number
  url: string | null
}

export interface ScoreHistory {
  id: string
  readiness_score: number
  recorded_at: string
  scoring_version: string
}

export interface DatasetDetail {
  id: string
  full_name: string
  display_name: string
  owner_name: string | null
  owner_contact: string | null
  intended_use: string | null
  limitations: string | null
  last_seen_at: string
  last_scored_at: string | null
  readiness_score: number
  readiness_status: string
  dimension_scores: DimensionScore[]
  reasons: Reason[]
  actions: Action[]
  score_history: ScoreHistory[]
}

export interface UpdateOwnerRequest {
  owner_name?: string
  owner_contact?: string
}

export interface UpdateMetadataRequest {
  display_name?: string
  intended_use?: string
  limitations?: string
}

/**
 * Fetch dataset list with optional filters
 */
export async function listDatasets(
  params: ListDatasetsParams = {}
): Promise<DatasetListResponse> {
  const searchParams = new URLSearchParams()
  if (params.status) searchParams.append('status', params.status)
  if (params.owner) searchParams.append('owner', params.owner)
  if (params.q) searchParams.append('q', params.q)

  const url = `${API_URL}/api/datasets${searchParams.toString() ? `?${searchParams.toString()}` : ''}`
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch datasets: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Fetch dataset detail by ID
 */
export async function getDatasetDetail(id: string): Promise<DatasetDetail> {
  const url = `${API_URL}/api/datasets/${id}`
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Dataset not found')
    }
    throw new Error(`Failed to fetch dataset: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Update dataset owner
 */
export async function updateOwner(
  id: string,
  data: UpdateOwnerRequest
): Promise<DatasetDetail> {
  const url = `${API_URL}/api/datasets/${id}/owner`
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(`Failed to update owner: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Update dataset metadata
 */
export async function updateMetadata(
  id: string,
  data: UpdateMetadataRequest
): Promise<DatasetDetail> {
  const url = `${API_URL}/api/datasets/${id}/metadata`
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    throw new Error(`Failed to update metadata: ${response.statusText}`)
  }

  return response.json()
}

// AI Assist endpoints

export interface DatasetDescriptionRequest {
  full_name: string
  display_name?: string
  owner_name?: string
  intended_use?: string
  limitations?: string
  column_names?: string[]
}

export interface DatasetDescriptionResponse {
  suggested_description: string
}

export interface ColumnDescriptionsRequest {
  dataset_name: string
  column_names: string[]
  existing_descriptions?: Record<string, string>
}

export interface ColumnDescriptionsResponse {
  suggested_descriptions: Record<string, string>
}

/**
 * Generate suggested dataset description
 */
export async function generateDatasetDescription(
  request: DatasetDescriptionRequest
): Promise<DatasetDescriptionResponse> {
  const url = `${API_URL}/api/ai/dataset-description`
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error('AI assist is not enabled')
    }
    throw new Error(`Failed to generate description: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Generate suggested column descriptions
 */
export async function generateColumnDescriptions(
  request: ColumnDescriptionsRequest
): Promise<ColumnDescriptionsResponse> {
  const url = `${API_URL}/api/ai/column-descriptions`
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error('AI assist is not enabled')
    }
    throw new Error(`Failed to generate descriptions: ${response.statusText}`)
  }

  return response.json()
}

