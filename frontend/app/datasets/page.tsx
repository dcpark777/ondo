'use client'

import { useEffect, useState, useRef } from 'react'
import Link from 'next/link'
import { listDatasets, DatasetListItem, ListDatasetsParams } from '../api/client'

type SortField = 'dataset' | 'score' | 'status' | 'owner' | 'last_scored'
type SortDirection = 'asc' | 'desc'

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<DatasetListItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter state
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const [statusDropdownOpen, setStatusDropdownOpen] = useState(false)
  const [ownerFilter, setOwnerFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const statusDropdownRef = useRef<HTMLDivElement>(null)
  
  // Sort state
  const [sortField, setSortField] = useState<SortField | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  // Fetch datasets
  const fetchDatasets = async () => {
    setLoading(true)
    setError(null)

    try {
      const params: ListDatasetsParams = {}
      if (statusFilter.length > 0) params.status = statusFilter.join(',')
      if (ownerFilter) params.owner = ownerFilter
      if (searchQuery) params.q = searchQuery

      const response = await listDatasets(params)
      setDatasets(response.datasets)
      setTotal(response.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load datasets')
      console.error('Error fetching datasets:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDatasets()
  }, [statusFilter, ownerFilter, searchQuery])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (statusDropdownRef.current && !statusDropdownRef.current.contains(event.target as Node)) {
        setStatusDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // Sort datasets
  const sortedDatasets = [...datasets].sort((a, b) => {
    if (!sortField) return 0
    
    let aValue: string | number
    let bValue: string | number
    
    switch (sortField) {
      case 'dataset':
        aValue = a.display_name || a.full_name
        bValue = b.display_name || b.full_name
        break
      case 'score':
        aValue = a.readiness_score
        bValue = b.readiness_score
        break
      case 'status':
        aValue = a.readiness_status
        bValue = b.readiness_status
        break
      case 'owner':
        aValue = a.owner_name || ''
        bValue = b.owner_name || ''
        break
      case 'last_scored':
        aValue = a.last_scored_at ? new Date(a.last_scored_at).getTime() : 0
        bValue = b.last_scored_at ? new Date(b.last_scored_at).getTime() : 0
        break
      default:
        return 0
    }
    
    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return (
        <span className="ml-1 text-gray-400">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
        </span>
      )
    }
    return (
      <span className="ml-1 text-blue-600">
        {sortDirection === 'asc' ? (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </span>
    )
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

  const getScoreBarColor = (status: string) => {
    switch (status) {
      case 'gold':
      case 'production_ready':
        return 'bg-green-500'
      case 'internal':
        return 'bg-orange-500'
      case 'draft':
        return 'bg-red-500'
      default:
        return 'bg-blue-500'
    }
  }

  const getLocationIcon = (locationType: string | null) => {
    if (!locationType) return null
    
    const type = locationType.toLowerCase()
    const iconClass = "w-4 h-4"
    
    switch (type) {
      case 's3':
        // AWS S3 bucket icon
        return (
          <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5zm0 2.18l8 4v8.64l-8 4.18-8-4.18V6.18l8-4z"/>
            <path d="M12 8L6 11v6l6 3 6-3v-6l-6-3zm0 2.18l3.5 1.75v3.14L12 16.82l-3.5-1.75v-3.14L12 10.18z"/>
          </svg>
        )
      case 'snowflake':
        // Snowflake logo - simplified snowflake pattern
        return (
          <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2l-2 2 2 2-2 2 2 2-2 2 2 2v4l-2-2-2 2-2-2-2 2-2-2v-4l2-2-2-2 2-2-2-2 2-2-2-2 2-2h4l-2 2 2-2 2 2 2-2 2 2zm0 2.83L9.17 8 12 10.83 14.83 8 12 4.83z"/>
            <circle cx="12" cy="12" r="1.5"/>
          </svg>
        )
      case 'databricks':
        // Databricks Unity Catalog logo - triangle pattern
        return (
          <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0L0 6.93v10.14L12 24l12-6.93V6.93L12 0zm0 2.31l9.23 5.33v8.72L12 21.69l-9.23-5.33V7.64L12 2.31z"/>
            <path d="M12 4.62L6.31 7.93v8.14L12 19.38l5.69-3.31V7.93L12 4.62zm0 2.31l3.46 2v4.14L12 15.38l-3.46-2.31V9.23L12 6.93z"/>
          </svg>
        )
      case 'bigquery':
        // Google BigQuery logo - simplified
        return (
          <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            <path d="M12 4c-4.41 0-8 3.59-8 8s3.59 8 8 8 8-3.59 8-8-3.59-8-8-8zm0 14c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6z"/>
          </svg>
        )
      case 'hive':
        // Apache Hive logo - hexagon/beehive pattern
        return (
          <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.83l7.5 3.75v7.5L12 19.17l-7.5-3.75v-7.5L12 4.83z"/>
            <path d="M12 7.5L8.5 9.5v5L12 16.5l3.5-2v-5L12 7.5zm0 2.25l1.75.875v2.25L12 13.75l-1.75-.875v-2.25L12 9.75z"/>
          </svg>
        )
      default:
        return (
          <svg className={iconClass} fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
          </svg>
        )
    }
  }

  const getLocationLabel = (locationType: string | null) => {
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

  const getLocationBadgeColor = (locationType: string | null) => {
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

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Datasets</h1>
        <p className="text-gray-600">
          {total} {total === 1 ? 'dataset' : 'datasets'} found
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Status Filter */}
          <div className="relative" ref={statusDropdownRef}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <button
              type="button"
              onClick={() => setStatusDropdownOpen(!statusDropdownOpen)}
              className="w-full px-3 py-2 text-left border border-gray-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 flex items-center justify-between"
            >
              <span className="text-sm text-gray-700">
                {statusFilter.length === 0
                  ? 'All'
                  : statusFilter.length === 1
                  ? getStatusLabel(statusFilter[0])
                  : `${statusFilter.length} selected`}
              </span>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${statusDropdownOpen ? 'transform rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {statusDropdownOpen && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                <div className="py-1">
                  <label className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={statusFilter.length === 0}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setStatusFilter([])
                        }
                      }}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">All</span>
                  </label>
                  {['gold', 'production_ready', 'internal', 'draft'].map((status) => (
                    <label key={status} className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={statusFilter.includes(status)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setStatusFilter([...statusFilter, status])
                          } else {
                            setStatusFilter(statusFilter.filter(s => s !== status))
                          }
                        }}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        {status === 'production_ready' ? 'Production Ready' : status.charAt(0).toUpperCase() + status.slice(1)}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Owner Filter */}
          <div>
            <label
              htmlFor="owner-filter"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Owner
            </label>
            <input
              id="owner-filter"
              type="text"
              value={ownerFilter}
              onChange={(e) => setOwnerFilter(e.target.value)}
              placeholder="Filter by owner..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Search */}
          <div>
            <label
              htmlFor="search"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Search
            </label>
            <input
              id="search"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search datasets..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading datasets...</p>
        </div>
      )}

      {/* Table */}
      {!loading && !error && (
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('dataset')}
                  >
                    <div className="flex items-center">
                      Dataset
                      {getSortIcon('dataset')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('score')}
                  >
                    <div className="flex items-center">
                      Score
                      {getSortIcon('score')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('status')}
                  >
                    <div className="flex items-center">
                      Status
                      {getSortIcon('status')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('owner')}
                  >
                    <div className="flex items-center">
                      Owner
                      {getSortIcon('owner')}
                    </div>
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('last_scored')}
                  >
                    <div className="flex items-center">
                      Last Scored
                      {getSortIcon('last_scored')}
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedDatasets.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                      No datasets found
                    </td>
                  </tr>
                ) : (
                  sortedDatasets.map((dataset) => (
                    <tr
                      key={dataset.id}
                      className="hover:bg-gray-50"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link
                          href={`/datasets/${dataset.id}`}
                          className="block hover:text-blue-600"
                        >
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {dataset.display_name}
                            </div>
                            <div className="text-sm text-gray-500">{dataset.full_name}</div>
                            {dataset.location_type && (
                              <div className="mt-1">
                                <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium ${getLocationBadgeColor(dataset.location_type)}`}>
                                  {getLocationIcon(dataset.location_type)}
                                  <span>{getLocationLabel(dataset.location_type)}</span>
                                </span>
                              </div>
                            )}
                          </div>
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="text-sm font-semibold text-gray-900">
                            {dataset.readiness_score}
                          </div>
                          <div className="ml-2 w-24 bg-gray-200 rounded-full h-2">
                            <div
                              className={`${getScoreBarColor(dataset.readiness_status)} h-2 rounded-full`}
                              style={{ width: `${dataset.readiness_score}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeClass(
                            dataset.readiness_status
                          )}`}
                        >
                          {getStatusLabel(dataset.readiness_status)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {dataset.owner_name || (
                          <span className="text-gray-400 italic">No owner</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(dataset.last_scored_at)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

