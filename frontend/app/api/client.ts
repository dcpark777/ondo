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
  location_type: string | null
  location_data: Record<string, any> | null
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
  measured: boolean  // Contract v1: Whether this dimension was measured
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

export interface Column {
  id: string
  name: string
  description: string | null
  type: string | null
  nullable: boolean | null
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
  description: string | null
  owner_name: string | null
  owner_contact: string | null
  intended_use: string | null
  limitations: string | null
  location_type: string | null
  location_data: Record<string, any> | null
  last_seen_at: string
  last_scored_at: string | null
  last_updated_at: string | null
  data_size_bytes: number | null
  file_count: number | null
  partition_keys: string[] | null
  sla_hours: number | null
  producing_job: string | null
  readiness_score: number
  readiness_status: string
  dimension_scores: DimensionScore[]
  reasons: Reason[]
  actions: Action[]
  columns: Column[]
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

export interface ApplyDescriptionRequest {
  dataset_id: string
  description: string
}

export interface ApplyColumnDescriptionsRequest {
  dataset_id: string
  column_descriptions: Record<string, string>
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

/**
 * Apply AI-generated dataset description
 */
export async function applyDatasetDescription(
  request: ApplyDescriptionRequest
): Promise<DatasetDetail> {
  const url = `${API_URL}/api/ai/apply-description`
  
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
    throw new Error(`Failed to apply description: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Apply AI-generated column descriptions
 */
export async function applyColumnDescriptions(
  request: ApplyColumnDescriptionsRequest
): Promise<DatasetDetail> {
  const url = `${API_URL}/api/ai/apply-column-descriptions`
  
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
    throw new Error(`Failed to apply column descriptions: ${response.statusText}`)
  }

  return response.json()
}


/**
 * Schema generation interfaces
 */
export interface SchemaGenerationResponse {
  schema: string
  test_code: string
  format: string
  dataset_name: string
}

/**
 * Generate Protocol Buffers schema for a dataset
 */
export async function generateProtobufSchema(id: string): Promise<SchemaGenerationResponse> {
  const url = `${API_URL}/api/datasets/${id}/schema/protobuf`
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to generate protobuf schema: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Generate Scala case class for a dataset
 */
export async function generateScalaSchema(id: string): Promise<SchemaGenerationResponse> {
  const url = `${API_URL}/api/datasets/${id}/schema/scala`
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to generate Scala schema: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Generate Python dataclass for a dataset
 */
export async function generatePythonSchema(id: string): Promise<SchemaGenerationResponse> {
  const url = `${API_URL}/api/datasets/${id}/schema/python`
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to generate Python schema: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Lineage interfaces
 */
export interface DatasetLineageItem {
  id: string
  full_name: string
  display_name: string
  transformation_type: string | null
}

export interface ColumnLineageItem {
  id: string
  upstream_column_id: string
  downstream_column_id: string
  upstream_column_name: string
  upstream_dataset_id: string
  upstream_dataset_name: string
  downstream_column_name: string
  downstream_dataset_id: string
  downstream_dataset_name: string
  transformation_expression: string | null
  created_at: string
}

export interface DatasetLineageResponse {
  upstream: DatasetLineageItem[]
  downstream: DatasetLineageItem[]
}

export interface ColumnLineageResponse {
  upstream: ColumnLineageItem[]
  downstream: ColumnLineageItem[]
}

/**
 * Get dataset lineage
 */
export async function getDatasetLineage(id: string): Promise<DatasetLineageResponse> {
  const url = `${API_URL}/api/datasets/${id}/lineage`
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to get dataset lineage: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get column lineage
 */
export async function getColumnLineage(datasetId: string, columnId: string): Promise<ColumnLineageResponse> {
  const url = `${API_URL}/api/datasets/${datasetId}/columns/${columnId}/lineage`
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to get column lineage: ${response.statusText}`)
  }

  return response.json()
}
