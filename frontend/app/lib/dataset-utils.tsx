/**
 * Shared dataset utility functions.
 *
 * Single source of truth for location/status/dimension helpers and formatters.
 * Import from here — never duplicate in components.
 */

import React from 'react'

// ---------------------------------------------------------------------------
// ACTION_KEY_TO_DIMENSION mapping (mirrors backend response_builder.py)
// ---------------------------------------------------------------------------
export const ACTION_KEY_TO_DIMENSION: Record<string, string> = {
  assign_owner: 'ownership',
  add_owner_contact: 'ownership',
  add_description: 'documentation',
  document_columns: 'documentation',
  fix_naming: 'schema_hygiene',
  reduce_nullable_columns: 'schema_hygiene',
  remove_legacy_columns: 'schema_hygiene',
  add_quality_checks: 'data_quality',
  define_sla: 'data_quality',
  resolve_failures: 'data_quality',
  prevent_breaking_changes: 'stability',
  add_changelog: 'stability',
  maintain_compatibility: 'stability',
  define_intended_use: 'operational',
  document_limitations: 'operational',
}

// ---------------------------------------------------------------------------
// Status helpers
// ---------------------------------------------------------------------------
export function getStatusBadgeClass(status: string): string {
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

export function getStatusLabel(status: string): string {
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

// ---------------------------------------------------------------------------
// Dimension helpers
// ---------------------------------------------------------------------------
export function getDimensionLabel(key: string): string {
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

// ---------------------------------------------------------------------------
// Location helpers
// ---------------------------------------------------------------------------
export function getLocationIcon(locationType: string | null): React.ReactNode {
  if (!locationType) return null

  const type = locationType.toLowerCase()
  const iconClass = 'w-4 h-4'

  switch (type) {
    case 's3':
      return (
        <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5zm0 2.18l8 4v8.64l-8 4.18-8-4.18V6.18l8-4z" />
          <path d="M12 8L6 11v6l6 3 6-3v-6l-6-3zm0 2.18l3.5 1.75v3.14L12 16.82l-3.5-1.75v-3.14L12 10.18z" />
        </svg>
      )
    case 'snowflake':
      return (
        <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2l1.41 1.41L12 4.83l-1.41-1.41L12 2zm0 20l-1.41-1.41L12 19.17l1.41 1.41L12 22zm9.9-9.9l-1.41 1.41L19.17 12l1.32-1.32 1.41-1.41zM2.1 12l1.41-1.41L4.83 12l-1.32 1.32L2.1 12zm16.97-4.97l1.41 1.41L18.36 9.64l-1.41-1.41 1.72-1.72zm-13.94 13.94l-1.41-1.41L5.64 14.36l1.41 1.41-1.72 1.72zm13.94 0l-1.72-1.72 1.41-1.41 1.72 1.72-1.41 1.41zm-13.94-13.94l1.72 1.72-1.41 1.41-1.72-1.72 1.41-1.41zM12 6l2.83 2.83L12 11.66 9.17 8.83 12 6zm0 12l-2.83-2.83L12 12.34l2.83 2.83L12 18zm6.36-6.36l2.83 2.83L18.36 16.24l-2.83-2.83 2.83-2.83zm-12.72 0l2.83-2.83 2.83 2.83-2.83 2.83-2.83-2.83z" />
        </svg>
      )
    case 'databricks':
      return (
        <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0L0 6.93v10.14L12 24l12-6.93V6.93L12 0zm0 2.31l9.23 5.33v8.72L12 21.69l-9.23-5.33V7.64L12 2.31z" />
          <path d="M12 4.62L6.31 7.93v8.14L12 19.38l5.69-3.31V7.93L12 4.62zm0 2.31l3.46 2v4.14L12 15.38l-3.46-2.31V9.23L12 6.93z" />
          <path d="M12 8.31l1.73 1v2.38L12 13.69l-1.73-1V9.31L12 8.31z" />
        </svg>
      )
    case 'bigquery':
      return (
        <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
        </svg>
      )
    case 'hive':
      return (
        <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.83l7.5 3.75v7.5L12 19.17l-7.5-3.75v-7.5L12 4.83z" />
          <path d="M12 7.5L8.5 9.5v5L12 16.5l3.5-2v-5L12 7.5zm0 2.25l1.75.875v2.25L12 13.75l-1.75-.875v-2.25L12 9.75z" />
          <path d="M12 10.5l-1.5.75v1.5L12 13.5l1.5-.75v-1.5L12 10.5z" />
        </svg>
      )
    default:
      return (
        <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
        </svg>
      )
  }
}

export function getLocationLabel(locationType: string | null): string {
  if (!locationType) return ''

  const type = locationType.toLowerCase()
  switch (type) {
    case 's3':
      return 'S3'
    case 'snowflake':
      return 'Snowflake'
    case 'databricks':
      return 'Databricks'
    case 'bigquery':
      return 'BigQuery'
    case 'hive':
      return 'Hive'
    default:
      return type.charAt(0).toUpperCase() + type.slice(1)
  }
}

export function getLocationBadgeColor(locationType: string | null): string {
  if (!locationType) return 'bg-gray-100 text-gray-600'

  const type = locationType.toLowerCase()
  switch (type) {
    case 's3':
      return 'bg-orange-100 text-orange-700'
    case 'snowflake':
      return 'bg-blue-100 text-blue-700'
    case 'databricks':
      return 'bg-purple-100 text-purple-700'
    case 'bigquery':
      return 'bg-yellow-100 text-yellow-700'
    case 'hive':
      return 'bg-green-100 text-green-700'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

// ---------------------------------------------------------------------------
// Formatters
// ---------------------------------------------------------------------------
export function formatDataSize(bytes: number | null): string {
  if (!bytes) return 'Unknown'
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`
}

export function formatSLA(hours: number | null): string {
  if (!hours) return 'Not specified'
  if (hours === 1) return 'Hourly'
  if (hours === 24) return 'Daily'
  if (hours === 168) return 'Weekly'
  if (hours === 720) return 'Monthly'
  return `Every ${hours} hours`
}
