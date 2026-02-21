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
  classification: string | null
  domain: string | null
  tags: string[]
}

export interface DatasetListResponse {
  datasets: DatasetListItem[]
  total: number
}

export interface ListDatasetsParams {
  status?: string
  owner?: string
  location_type?: string
  classification?: string
  domain?: string
  tag?: string
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
  created_at: string
  created_by: string | null
  last_seen_at: string
  last_scored_at: string | null
  last_updated_at: string | null
  updated_by: string | null
  data_size_bytes: number | null
  file_count: number | null
  partition_keys: string[] | null
  sla_hours: number | null
  producing_job: string | null
  readiness_score: number
  readiness_status: string
  classification: string | null
  domain: string | null
  tags: string[]
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
  if (params.location_type) searchParams.append('location_type', params.location_type)
  if (params.classification) searchParams.append('classification', params.classification)
  if (params.domain) searchParams.append('domain', params.domain)
  if (params.tag) searchParams.append('tag', params.tag)
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

// Lineage Graph
export interface LineageGraphNode {
  id: string
  full_name: string
  display_name: string
  readiness_score: number
  readiness_status: string
  is_current: boolean
}

export interface LineageGraphEdge {
  source: string
  target: string
  transformation_type: string | null
}

export interface LineageGraph {
  nodes: LineageGraphNode[]
  edges: LineageGraphEdge[]
  root_id: string
}

export async function getLineageGraph(datasetId: string, depth: number = 2): Promise<LineageGraph> {
  const url = `${API_URL}/api/datasets/${datasetId}/lineage/graph?depth=${depth}`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch lineage graph: ${response.statusText}`)
  return response.json()
}

// Impact Analysis
export interface ImpactedDataset {
  id: string
  full_name: string
  display_name: string
  readiness_score: number
  readiness_status: string
  depth: number
  path: string[]
}

export interface ImpactAnalysis {
  dataset_id: string
  dataset_name: string
  depth: number
  total_impacted: number
  impacted: ImpactedDataset[]
}

export async function getImpactAnalysis(datasetId: string, depth: number = 3): Promise<ImpactAnalysis> {
  const url = `${API_URL}/api/datasets/${datasetId}/impact?depth=${depth}`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch impact analysis: ${response.statusText}`)
  return response.json()
}

/**
 * Tags & Classification
 */

export interface UpdateTagsRequest {
  tags: string[]
}

export interface UpdateClassificationRequest {
  classification?: string | null
  domain?: string | null
}

export async function updateTags(id: string, data: UpdateTagsRequest): Promise<DatasetDetail> {
  const url = `${API_URL}/api/datasets/${id}/tags`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to update tags: ${response.statusText}`)
  return response.json()
}

export async function updateClassification(id: string, data: UpdateClassificationRequest): Promise<DatasetDetail> {
  const url = `${API_URL}/api/datasets/${id}/classification`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to update classification: ${response.statusText}`)
  return response.json()
}

export async function listAllTags(): Promise<string[]> {
  const url = `${API_URL}/api/datasets/meta/tags`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to list tags: ${response.statusText}`)
  return response.json()
}

export async function listAllDomains(): Promise<string[]> {
  const url = `${API_URL}/api/datasets/meta/domains`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to list domains: ${response.statusText}`)
  return response.json()
}

/**
 * Dashboard
 */

export interface DashboardSummary {
  total_datasets: number
  average_score: number
  status_distribution: Record<string, number>
  score_distribution: Record<string, number>
  top_actions: {
    action_key: string
    title: string
    total_gain: number
    dataset_count: number
  }[]
  lowest_scoring: {
    id: string
    display_name: string
    full_name: string
    readiness_score: number
    readiness_status: string
  }[]
  recently_scored: {
    id: string
    display_name: string
    full_name: string
    readiness_score: number
    readiness_status: string
    last_scored_at: string | null
  }[]
  dimension_health: Record<string, number>
}

export interface DashboardTrends {
  days: number
  trends: {
    date: string
    avg_score: number
    count: number
  }[]
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const url = `${API_URL}/api/dashboard/summary`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch dashboard summary: ${response.statusText}`)
  return response.json()
}

export async function getDashboardTrends(days: number = 30): Promise<DashboardTrends> {
  const url = `${API_URL}/api/dashboard/trends?days=${days}`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch dashboard trends: ${response.statusText}`)
  return response.json()
}

/**
 * Quality Rules
 */

export interface QualityRuleExecution {
  id: string
  rule_id: string
  dataset_id: string
  passed: boolean
  records_checked: number | null
  records_failed: number | null
  error_message: string | null
  executed_at: string
}

export interface QualityRule {
  id: string
  dataset_id: string
  name: string
  description: string | null
  rule_type: string
  column_name: string | null
  parameters: Record<string, any> | null
  severity: string
  enabled: boolean
  created_at: string
  created_by: string | null
  latest_execution: QualityRuleExecution | null
}

export interface QualityRuleCreateRequest {
  name: string
  description?: string
  rule_type: string
  column_name?: string
  parameters?: Record<string, any>
  severity?: string
  enabled?: boolean
  created_by?: string
}

export interface QualityRuleUpdateRequest {
  name?: string
  description?: string
  rule_type?: string
  column_name?: string
  parameters?: Record<string, any>
  severity?: string
  enabled?: boolean
}

export interface QualityRuleExecutionCreateRequest {
  passed: boolean
  records_checked?: number
  records_failed?: number
  error_message?: string
}

export interface BatchExecutionItem {
  rule_id: string
  passed: boolean
  records_checked?: number
  records_failed?: number
  error_message?: string
}

export interface BatchExecutionRequest {
  executions: BatchExecutionItem[]
}

/**
 * List quality rules for a dataset
 */
export async function listQualityRules(datasetId: string): Promise<QualityRule[]> {
  const url = `${API_URL}/api/datasets/${datasetId}/quality-rules`
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
  })
  if (!response.ok) throw new Error(`Failed to fetch quality rules: ${response.statusText}`)
  return response.json()
}

/**
 * Create a quality rule for a dataset
 */
export async function createQualityRule(
  datasetId: string,
  data: QualityRuleCreateRequest
): Promise<QualityRule> {
  const url = `${API_URL}/api/datasets/${datasetId}/quality-rules`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to create quality rule: ${response.statusText}`)
  return response.json()
}

/**
 * Update a quality rule
 */
export async function updateQualityRule(
  datasetId: string,
  ruleId: string,
  data: QualityRuleUpdateRequest
): Promise<QualityRule> {
  const url = `${API_URL}/api/datasets/${datasetId}/quality-rules/${ruleId}`
  const response = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to update quality rule: ${response.statusText}`)
  return response.json()
}

/**
 * Delete a quality rule
 */
export async function deleteQualityRule(
  datasetId: string,
  ruleId: string
): Promise<void> {
  const url = `${API_URL}/api/datasets/${datasetId}/quality-rules/${ruleId}`
  const response = await fetch(url, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
  })
  if (!response.ok) throw new Error(`Failed to delete quality rule: ${response.statusText}`)
}

/**
 * Record an execution result for a quality rule
 */
export async function recordRuleExecution(
  datasetId: string,
  ruleId: string,
  data: QualityRuleExecutionCreateRequest
): Promise<QualityRuleExecution> {
  const url = `${API_URL}/api/datasets/${datasetId}/quality-rules/${ruleId}/execute`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to record execution: ${response.statusText}`)
  return response.json()
}

/**
 * Record batch execution results
 */
export async function recordBatchExecution(
  datasetId: string,
  data: BatchExecutionRequest
): Promise<QualityRuleExecution[]> {
  const url = `${API_URL}/api/datasets/${datasetId}/quality-rules/execute-batch`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to record batch execution: ${response.statusText}`)
  return response.json()
}

/**
 * Get execution history for a quality rule
 */
export async function getExecutionHistory(
  datasetId: string,
  ruleId: string,
  limit: number = 30
): Promise<QualityRuleExecution[]> {
  const url = `${API_URL}/api/datasets/${datasetId}/quality-rules/${ruleId}/history?limit=${limit}`
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
  })
  if (!response.ok) throw new Error(`Failed to fetch execution history: ${response.statusText}`)
  return response.json()
}

/**
 * Data Profiling
 */

export interface ColumnProfile {
  id: string
  column_id: string
  dataset_id: string
  column_name: string
  row_count: number | null
  null_count: number | null
  null_percentage: number | null
  distinct_count: number | null
  distinct_percentage: number | null
  min_value: string | null
  max_value: string | null
  mean_value: number | null
  median_value: number | null
  stddev_value: number | null
  min_length: number | null
  max_length: number | null
  avg_length: number | null
  top_values: { value: string; count: number }[] | null
  sample_values: any[] | null
  profiled_at: string
}

export interface ColumnProfileSubmit {
  column_name: string
  row_count?: number
  null_count?: number
  null_percentage?: number
  distinct_count?: number
  distinct_percentage?: number
  min_value?: string
  max_value?: string
  mean_value?: number
  median_value?: number
  stddev_value?: number
  min_length?: number
  max_length?: number
  avg_length?: number
  top_values?: { value: string; count: number }[]
  sample_values?: any[]
}

export async function getDatasetProfiles(datasetId: string): Promise<ColumnProfile[]> {
  const url = `${API_URL}/api/datasets/${datasetId}/profiles`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch profiles: ${response.statusText}`)
  return response.json()
}

export async function submitProfiles(datasetId: string, profiles: ColumnProfileSubmit[]): Promise<ColumnProfile[]> {
  const url = `${API_URL}/api/datasets/${datasetId}/profiles`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profiles }),
  })
  if (!response.ok) throw new Error(`Failed to submit profiles: ${response.statusText}`)
  return response.json()
}

export async function getProfileHistory(datasetId: string, columnName: string, limit: number = 10): Promise<ColumnProfile[]> {
  const url = `${API_URL}/api/datasets/${datasetId}/profiles/history?column_name=${encodeURIComponent(columnName)}&limit=${limit}`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch profile history: ${response.statusText}`)
  return response.json()
}

/**
 * Business Glossary
 */

export interface GlossaryTerm {
  id: string
  name: string
  definition: string
  domain: string | null
  owner: string | null
  status: string
  created_at: string
  updated_at: string
  linked_columns_count: number
  linked_columns: {
    link_id: string
    column_id: string
    column_name: string
    dataset_id: string
    dataset_name: string
  }[]
}

export interface GlossaryTermCreateRequest {
  name: string
  definition: string
  domain?: string
  owner?: string
  status?: string
}

export interface GlossaryTermUpdateRequest {
  name?: string
  definition?: string
  domain?: string
  owner?: string
  status?: string
}

export async function listGlossaryTerms(params?: { q?: string; domain?: string; status?: string }): Promise<GlossaryTerm[]> {
  const searchParams = new URLSearchParams()
  if (params?.q) searchParams.append('q', params.q)
  if (params?.domain) searchParams.append('domain', params.domain)
  if (params?.status) searchParams.append('status', params.status)
  const url = `${API_URL}/api/glossary${searchParams.toString() ? `?${searchParams.toString()}` : ''}`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch glossary terms: ${response.statusText}`)
  return response.json()
}

export async function createGlossaryTerm(data: GlossaryTermCreateRequest): Promise<GlossaryTerm> {
  const url = `${API_URL}/api/glossary`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to create glossary term: ${response.statusText}`)
  return response.json()
}

export async function getGlossaryTerm(termId: string): Promise<GlossaryTerm> {
  const url = `${API_URL}/api/glossary/${termId}`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch glossary term: ${response.statusText}`)
  return response.json()
}

export async function updateGlossaryTerm(termId: string, data: GlossaryTermUpdateRequest): Promise<GlossaryTerm> {
  const url = `${API_URL}/api/glossary/${termId}`
  const response = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to update glossary term: ${response.statusText}`)
  return response.json()
}

export async function deleteGlossaryTerm(termId: string): Promise<void> {
  const url = `${API_URL}/api/glossary/${termId}`
  const response = await fetch(url, { method: 'DELETE' })
  if (!response.ok) throw new Error(`Failed to delete glossary term: ${response.statusText}`)
}

export async function linkTermToColumn(termId: string, columnId: string): Promise<void> {
  const url = `${API_URL}/api/glossary/${termId}/columns/${columnId}`
  const response = await fetch(url, { method: 'POST' })
  if (!response.ok) throw new Error(`Failed to link term to column: ${response.statusText}`)
}

export async function unlinkTermFromColumn(termId: string, columnId: string): Promise<void> {
  const url = `${API_URL}/api/glossary/${termId}/columns/${columnId}`
  const response = await fetch(url, { method: 'DELETE' })
  if (!response.ok) throw new Error(`Failed to unlink term from column: ${response.statusText}`)
}

/**
 * Facets
 */

export interface DatasetFacets {
  status: Record<string, number>
  classification: Record<string, number>
  domain: Record<string, number>
  location_type: Record<string, number>
  tags: Record<string, number>
}

export async function getDatasetFacets(): Promise<DatasetFacets> {
  const url = `${API_URL}/api/datasets/meta/facets`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch facets: ${response.statusText}`)
  return response.json()
}

/**
 * Watches & Notifications
 */

export interface NotificationItem {
  id: string
  dataset_id: string
  user_id: string
  notification_type: string
  title: string
  message: string
  read: boolean
  created_at: string
}

export async function checkWatch(datasetId: string, userId: string): Promise<{ watching: boolean }> {
  const url = `${API_URL}/api/datasets/${datasetId}/watch?user_id=${encodeURIComponent(userId)}`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to check watch: ${response.statusText}`)
  return response.json()
}

export async function startWatching(datasetId: string, userId: string): Promise<{ watching: boolean }> {
  const url = `${API_URL}/api/datasets/${datasetId}/watch?user_id=${encodeURIComponent(userId)}`
  const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to start watching: ${response.statusText}`)
  return response.json()
}

export async function stopWatching(datasetId: string, userId: string): Promise<{ watching: boolean }> {
  const url = `${API_URL}/api/datasets/${datasetId}/watch?user_id=${encodeURIComponent(userId)}`
  const response = await fetch(url, { method: 'DELETE', headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to stop watching: ${response.statusText}`)
  return response.json()
}

export async function listNotifications(userId: string, unreadOnly: boolean = false): Promise<NotificationItem[]> {
  const url = `${API_URL}/api/notifications?user_id=${encodeURIComponent(userId)}${unreadOnly ? '&unread_only=true' : ''}`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch notifications: ${response.statusText}`)
  return response.json()
}

export async function markNotificationRead(notificationId: string): Promise<void> {
  const url = `${API_URL}/api/notifications/${notificationId}/read`
  const response = await fetch(url, { method: 'POST' })
  if (!response.ok) throw new Error(`Failed to mark notification as read: ${response.statusText}`)
}

export async function markAllNotificationsRead(userId: string): Promise<void> {
  const url = `${API_URL}/api/notifications/read-all?user_id=${encodeURIComponent(userId)}`
  const response = await fetch(url, { method: 'POST' })
  if (!response.ok) throw new Error(`Failed to mark all as read: ${response.statusText}`)
}

// Usage Metrics

export interface ViewStats {
  dataset_id: string
  days: number
  total_views: number
  unique_viewers: number
  daily_views: { date: string; count: number }[]
  recent_viewers: { user_id: string; last_viewed: string }[]
}

export interface PopularDataset {
  id: string
  full_name: string
  display_name: string
  readiness_score: number
  readiness_status: string
  view_count: number
  unique_viewers: number
}

export async function recordDatasetView(datasetId: string, userId: string): Promise<void> {
  const url = `${API_URL}/api/datasets/${datasetId}/views?user_id=${encodeURIComponent(userId)}`
  await fetch(url, { method: 'POST' })
}

export async function getViewStats(datasetId: string, days: number = 30): Promise<ViewStats> {
  const url = `${API_URL}/api/datasets/${datasetId}/views/stats?days=${days}`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch view stats: ${response.statusText}`)
  return response.json()
}

export async function getPopularDatasets(days: number = 30, limit: number = 10): Promise<{ days: number; datasets: PopularDataset[] }> {
  const url = `${API_URL}/api/datasets/popular?days=${days}&limit=${limit}`
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' } })
  if (!response.ok) throw new Error(`Failed to fetch popular datasets: ${response.statusText}`)
  return response.json()
}

// Bulk Operations

export interface BulkTagRequest {
  dataset_ids: string[]
  tags: string[]
  mode: 'add' | 'remove' | 'replace'
}

export interface BulkClassificationRequest {
  dataset_ids: string[]
  classification?: string | null
  domain?: string | null
}

export interface BulkOperationResult {
  updated: number
  dataset_ids: string[]
}

export async function bulkUpdateTags(data: BulkTagRequest): Promise<BulkOperationResult> {
  const url = `${API_URL}/api/bulk/tags`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to bulk update tags: ${response.statusText}`)
  return response.json()
}

export async function bulkUpdateClassification(data: BulkClassificationRequest): Promise<BulkOperationResult> {
  const url = `${API_URL}/api/bulk/classification`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error(`Failed to bulk update classification: ${response.statusText}`)
  return response.json()
}
