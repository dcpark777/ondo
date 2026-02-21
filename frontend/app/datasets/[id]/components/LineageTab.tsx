'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { DatasetDetail, getDatasetLineage, getColumnLineage, DatasetLineageResponse, ColumnLineageResponse } from '../../../api/client'

interface LineageTabProps {
  dataset: DatasetDetail
}

export default function LineageTab({ dataset }: LineageTabProps) {
  const [datasetLineage, setDatasetLineage] = useState<DatasetLineageResponse | null>(null)
  const [loadingLineage, setLoadingLineage] = useState(false)
  const [columnLineageMap, setColumnLineageMap] = useState<Record<string, ColumnLineageResponse>>({})
  const [loadingColumnLineage, setLoadingColumnLineage] = useState<Record<string, boolean>>({})

  // Load dataset lineage on mount
  useEffect(() => {
    if (!datasetLineage && !loadingLineage) {
      setLoadingLineage(true)
      getDatasetLineage(dataset.id)
        .then(setDatasetLineage)
        .catch(err => {
          console.error('Failed to load dataset lineage:', err)
          setDatasetLineage({ upstream: [], downstream: [] })
        })
        .finally(() => setLoadingLineage(false))
    }
  }, [dataset.id, datasetLineage, loadingLineage])

  // Load column lineage for all columns
  useEffect(() => {
    if (dataset.columns && dataset.columns.length > 0) {
      dataset.columns.forEach((column) => {
        if (!columnLineageMap[column.id] && !loadingColumnLineage[column.id]) {
          setLoadingColumnLineage(prev => ({ ...prev, [column.id]: true }))
          getColumnLineage(dataset.id, column.id)
            .then((lineage) => {
              setColumnLineageMap(prev => ({ ...prev, [column.id]: lineage }))
            })
            .catch(err => {
              console.error(`Failed to load column lineage for ${column.name}:`, err)
              setColumnLineageMap(prev => ({ ...prev, [column.id]: { upstream: [], downstream: [] } }))
            })
            .finally(() => {
              setLoadingColumnLineage(prev => ({ ...prev, [column.id]: false }))
            })
        }
      })
    }
  }, [dataset.id, dataset.columns, columnLineageMap, loadingColumnLineage])

  return (
    <div className="space-y-6">
      {/* Dataset Lineage Graph */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Dataset Lineage</h2>

        {loadingLineage ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading lineage...</p>
          </div>
        ) : datasetLineage ? (
          <div className="relative">
            <div className="flex items-center justify-between min-h-[300px]">
              {/* Downstream Section - Left */}
              <div className="flex-1 flex flex-col items-end pr-8">
                {datasetLineage.downstream.length > 0 ? (
                  <div className="space-y-4 w-full max-w-xs">
                    <h3 className="text-sm font-medium text-gray-500 mb-4 text-right">Downstream</h3>
                    {datasetLineage.downstream.map((item) => (
                      <div key={item.id} className="relative">
                        <div className="absolute right-0 top-1/2 w-8 h-0.5 bg-green-400 transform -translate-y-1/2"></div>
                        <div className="absolute right-8 top-1/2 w-0.5 h-8 bg-green-400 transform -translate-y-1/2"></div>
                        <div className="bg-green-50 border-2 border-green-300 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                          <Link href={`/datasets/${item.id}`} className="block group">
                            <div className="text-sm font-semibold text-green-700 group-hover:text-green-900 mb-1">
                              {item.display_name}
                            </div>
                            <div className="text-xs text-gray-600 truncate">{item.full_name}</div>
                            {item.transformation_type && (
                              <div className="mt-2">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                  {item.transformation_type}
                                </span>
                              </div>
                            )}
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-400 text-sm">
                    <p>No downstream dependencies</p>
                  </div>
                )}
              </div>

              {/* Center - Current Dataset */}
              <div className="flex-shrink-0 relative z-10">
                <div className="bg-gradient-to-br from-blue-500 to-blue-600 border-4 border-blue-700 rounded-xl p-6 shadow-lg min-w-[200px]">
                  <div className="text-center">
                    <div className="text-white font-bold text-lg mb-1">{dataset.display_name}</div>
                    <div className="text-blue-100 text-xs mb-3 truncate">{dataset.full_name}</div>
                    <div className="inline-flex items-center px-3 py-1 rounded-full bg-white/20 backdrop-blur-sm">
                      <span className="text-white text-xs font-medium">Current Dataset</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Upstream Section - Right */}
              <div className="flex-1 flex flex-col items-start pl-8">
                {datasetLineage.upstream.length > 0 ? (
                  <div className="space-y-4 w-full max-w-xs">
                    <h3 className="text-sm font-medium text-gray-500 mb-4">Upstream</h3>
                    {datasetLineage.upstream.map((item) => (
                      <div key={item.id} className="relative">
                        <div className="absolute left-0 top-1/2 w-8 h-0.5 bg-blue-400 transform -translate-y-1/2"></div>
                        <div className="absolute left-8 top-1/2 w-0.5 h-8 bg-blue-400 transform -translate-y-1/2"></div>
                        <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                          <Link href={`/datasets/${item.id}`} className="block group">
                            <div className="text-sm font-semibold text-blue-700 group-hover:text-blue-900 mb-1">
                              {item.display_name}
                            </div>
                            <div className="text-xs text-gray-600 truncate">{item.full_name}</div>
                            {item.transformation_type && (
                              <div className="mt-2">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                  {item.transformation_type}
                                </span>
                              </div>
                            )}
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-400 text-sm">
                    <p>No upstream dependencies</p>
                  </div>
                )}
              </div>
            </div>

            {/* Empty State */}
            {datasetLineage.upstream.length === 0 && datasetLineage.downstream.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <div className="mb-4">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                </div>
                <p className="text-sm font-medium">No lineage information available</p>
                <p className="text-xs text-gray-400 mt-1">This dataset has no upstream or downstream dependencies</p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p className="text-sm">No lineage information available</p>
          </div>
        )}
      </div>

      {/* Column Lineage */}
      {dataset.columns && dataset.columns.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Column Lineage</h2>

          <div className="space-y-6">
            {dataset.columns.map((column) => {
              const columnLineage = columnLineageMap[column.id]
              const isLoading = loadingColumnLineage[column.id]
              const hasLineage = columnLineage && (columnLineage.upstream.length > 0 || columnLineage.downstream.length > 0)

              if (!hasLineage && !isLoading) {
                return null
              }

              return (
                <div key={column.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="mb-4">
                    <h3 className="text-lg font-medium text-gray-900">{column.name}</h3>
                    {column.type && <p className="text-sm text-gray-500 mt-1">{column.type}</p>}
                  </div>

                  {isLoading ? (
                    <div className="text-center py-4">
                      <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                      <p className="mt-2 text-sm text-gray-600">Loading lineage...</p>
                    </div>
                  ) : columnLineage ? (
                    <div className="space-y-4">
                      {columnLineage.upstream.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-3">From Columns</h4>
                          <div className="space-y-2">
                            {columnLineage.upstream.map((item) => (
                              <div key={item.id} className="bg-blue-50 border border-blue-200 rounded-md p-3">
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <div className="flex items-center space-x-2">
                                      <span className="text-sm font-medium text-blue-700">{item.upstream_column_name}</span>
                                      <span className="text-xs text-gray-500">from</span>
                                      <Link href={`/datasets/${item.upstream_dataset_id}`} className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                                        {item.upstream_dataset_name}
                                      </Link>
                                    </div>
                                    {item.transformation_expression && (
                                      <div className="mt-2 text-xs text-gray-600 font-mono bg-white px-2 py-1 rounded border border-gray-200">
                                        {item.transformation_expression}
                                      </div>
                                    )}
                                  </div>
                                  <div className="ml-2">
                                    <span className="text-xs text-blue-600">→</span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {columnLineage.downstream.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-3">To Columns</h4>
                          <div className="space-y-2">
                            {columnLineage.downstream.map((item) => (
                              <div key={item.id} className="bg-green-50 border border-green-200 rounded-md p-3">
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <div className="flex items-center space-x-2">
                                      <span className="text-xs text-green-600">→</span>
                                      <span className="text-sm font-medium text-green-700">{item.downstream_column_name}</span>
                                      <span className="text-xs text-gray-500">in</span>
                                      <Link href={`/datasets/${item.downstream_dataset_id}`} className="text-xs text-green-600 hover:text-green-800 font-medium">
                                        {item.downstream_dataset_name}
                                      </Link>
                                    </div>
                                    {item.transformation_expression && (
                                      <div className="mt-2 text-xs text-gray-600 font-mono bg-white px-2 py-1 rounded border border-gray-200">
                                        {item.transformation_expression}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {columnLineage.upstream.length === 0 && columnLineage.downstream.length === 0 && (
                        <div className="text-center py-4 text-gray-400 text-sm">
                          No lineage information for this column
                        </div>
                      )}
                    </div>
                  ) : null}
                </div>
              )
            })}

            {/* Show message if no columns have lineage */}
            {dataset.columns.every(col => {
              const lineage = columnLineageMap[col.id]
              return !lineage || (lineage.upstream.length === 0 && lineage.downstream.length === 0)
            }) && !dataset.columns.some(col => loadingColumnLineage[col.id]) && (
              <div className="text-center py-8 text-gray-500">
                <p className="text-sm">No column-level lineage information available</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
