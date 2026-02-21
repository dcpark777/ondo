'use client'

import { DatasetDetail } from '../../../api/client'
import {
  getLocationIcon,
  getLocationLabel,
  getLocationBadgeColor,
} from '../../../lib/dataset-utils'

interface DetailsTabProps {
  dataset: DatasetDetail
}

function formatLocation(dataset: DatasetDetail) {
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
        display: [data.catalog, data.schema || data.database, data.table].filter(Boolean).join('.') || 'Databricks Location',
        details: [
          { label: 'Catalog', value: data.catalog },
          { label: 'Schema', value: data.schema || data.database },
          { label: 'Table', value: data.table },
        ].filter(item => item.value),
      }
    case 'snowflake':
      return {
        label: 'Snowflake',
        display: [data.database, data.schema, data.table].filter(Boolean).join('.') || 'Snowflake Location',
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
        display: [data.project, data.dataset, data.table].filter(Boolean).join('.') || 'BigQuery Location',
        details: [
          { label: 'Project', value: data.project },
          { label: 'Dataset', value: data.dataset },
          { label: 'Table', value: data.table },
        ].filter(item => item.value),
      }
    case 'hive':
      return {
        label: 'Hive',
        display: [data.database, data.table].filter(Boolean).join('.') || 'Hive Location',
        details: [
          { label: 'Database', value: data.database },
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

export default function DetailsTab({ dataset }: DetailsTabProps) {
  const locationInfo = formatLocation(dataset)

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Dataset Details</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Storage Location */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Storage Location</h3>
          {locationInfo ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${getLocationBadgeColor(dataset.location_type)}`}>
                  {getLocationIcon(dataset.location_type)}
                  <span>{getLocationLabel(dataset.location_type)}</span>
                </span>
              </div>
              <div className="text-sm text-gray-900 font-mono bg-gray-50 p-2 rounded">
                {locationInfo.display}
              </div>
              {locationInfo.details && locationInfo.details.length > 0 && (
                <div className="mt-2 space-y-1">
                  {locationInfo.details.map((detail, idx) => (
                    <div key={idx} className="text-sm text-gray-600">
                      <span className="font-medium">{detail.label}:</span> {detail.value}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-400">Not specified</p>
          )}
        </div>

        {/* Created At */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Created At</h3>
          <p className="text-sm text-gray-900">
            {dataset.created_at
              ? new Date(dataset.created_at).toLocaleString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  timeZoneName: 'short',
                })
              : 'Not available'}
          </p>
        </div>

        {/* Created By */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Created By</h3>
          <p className="text-sm text-gray-900">
            {dataset.created_by || <span className="text-gray-400">Not specified</span>}
          </p>
        </div>

        {/* Last Updated At */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Last Updated At</h3>
          <p className="text-sm text-gray-900">
            {dataset.last_updated_at
              ? new Date(dataset.last_updated_at).toLocaleString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  timeZoneName: 'short',
                })
              : <span className="text-gray-400">Not available</span>}
          </p>
        </div>

        {/* Updated By */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-2">Last Updated By</h3>
          <p className="text-sm text-gray-900">
            {dataset.updated_by || <span className="text-gray-400">Not specified</span>}
          </p>
        </div>
      </div>
    </div>
  )
}
