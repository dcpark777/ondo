'use client'

import { useEffect, useState, useRef } from 'react'
import Link from 'next/link'
import { listDatasets, DatasetListItem, ListDatasetsParams, getDatasetFacets, DatasetFacets, bulkUpdateTags, bulkUpdateClassification } from '../api/client'
import {
  getStatusBadgeClass,
  getStatusLabel,
  getLocationIcon,
  getLocationLabel,
  getLocationBadgeColor,
  getClassificationBadgeClass,
  getClassificationLabel,
} from '../lib/dataset-utils'

type SortField = 'dataset' | 'score' | 'status' | 'owner' | 'last_scored'
type SortDirection = 'asc' | 'desc'

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<DatasetListItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Bulk selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [bulkTagInput, setBulkTagInput] = useState('')
  const [bulkTagMode, setBulkTagMode] = useState<'add' | 'remove' | 'replace'>('add')
  const [bulkClassification, setBulkClassification] = useState('')
  const [bulkDomain, setBulkDomain] = useState('')
  const [bulkActionType, setBulkActionType] = useState<'tags' | 'classification' | null>(null)

  // Filter state
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const [statusDropdownOpen, setStatusDropdownOpen] = useState(false)
  const [ownerFilter, setOwnerFilter] = useState<string[]>([])
  const [ownerDropdownOpen, setOwnerDropdownOpen] = useState(false)
  const [ownerSearchQuery, setOwnerSearchQuery] = useState<string>('')
  const [locationFilter, setLocationFilter] = useState<string[]>([])
  const [locationDropdownOpen, setLocationDropdownOpen] = useState(false)
  const [classificationFilter, setClassificationFilter] = useState<string[]>([])
  const [classificationDropdownOpen, setClassificationDropdownOpen] = useState(false)
  const [domainFilter, setDomainFilter] = useState<string[]>([])
  const [domainDropdownOpen, setDomainDropdownOpen] = useState(false)
  const [tagFilter, setTagFilter] = useState<string[]>([])
  const [tagDropdownOpen, setTagDropdownOpen] = useState(false)
  const [datasetFilter, setDatasetFilter] = useState<string[]>([])
  const [datasetDropdownOpen, setDatasetDropdownOpen] = useState(false)
  const [datasetSearchQuery, setDatasetSearchQuery] = useState<string>('')
  const statusDropdownRef = useRef<HTMLDivElement>(null)
  const ownerDropdownRef = useRef<HTMLDivElement>(null)
  const locationDropdownRef = useRef<HTMLDivElement>(null)
  const classificationDropdownRef = useRef<HTMLDivElement>(null)
  const domainDropdownRef = useRef<HTMLDivElement>(null)
  const tagDropdownRef = useRef<HTMLDivElement>(null)
  const datasetDropdownRef = useRef<HTMLDivElement>(null)
  
  // Sort state
  const [sortField, setSortField] = useState<SortField | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  // Facets state
  const [facets, setFacets] = useState<DatasetFacets | null>(null)

  useEffect(() => {
    getDatasetFacets().then(setFacets).catch(() => {})
  }, [])

  // Fetch datasets
  const fetchDatasets = async () => {
    setLoading(true)
    setError(null)

    try {
      const params: ListDatasetsParams = {}
      if (statusFilter.length > 0) params.status = statusFilter.join(',')
      if (ownerFilter.length > 0) params.owner = ownerFilter.join(',')
      if (locationFilter.length > 0) params.location_type = locationFilter.join(',')
      if (classificationFilter.length > 0) params.classification = classificationFilter.join(',')
      if (domainFilter.length > 0) params.domain = domainFilter.join(',')
      if (tagFilter.length > 0) params.tag = tagFilter.join(',')
      if (datasetFilter.length > 0) params.q = datasetFilter.join(',')

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
  }, [statusFilter, ownerFilter, locationFilter, classificationFilter, domainFilter, tagFilter, datasetFilter])

  // Get unique owners from datasets
  const uniqueOwners = Array.from(
    new Set(datasets.map(d => d.owner_name).filter((name): name is string => Boolean(name)))
  ).sort()
  
  // Get unique location types from datasets
  const uniqueLocationTypes = Array.from(
    new Set(datasets.map(d => d.location_type).filter((type): type is string => Boolean(type)))
  ).sort()

  // Get unique classifications from datasets
  const uniqueClassifications = Array.from(
    new Set(datasets.map(d => d.classification).filter((c): c is string => Boolean(c)))
  ).sort()

  // Get unique domains from datasets
  const uniqueDomains = Array.from(
    new Set(datasets.map(d => d.domain).filter((d): d is string => Boolean(d)))
  ).sort()

  // Get unique tags from datasets
  const uniqueTags = Array.from(
    new Set(datasets.flatMap(d => d.tags || []))
  ).sort()

  // Filter owners based on search query
  const filteredOwners = ownerSearchQuery
    ? uniqueOwners.filter(owner => owner.toLowerCase().includes(ownerSearchQuery.toLowerCase()))
    : uniqueOwners

  // Get unique dataset names (display_name and full_name) for search
  const uniqueDatasets = Array.from(
    new Set(
      datasets.flatMap(d => [
        d.display_name,
        d.full_name
      ]).filter(Boolean)
    )
  ).sort()

  // Filter datasets based on search query
  const filteredDatasets = datasetSearchQuery
    ? uniqueDatasets.filter(dataset => 
        dataset.toLowerCase().includes(datasetSearchQuery.toLowerCase())
      )
    : uniqueDatasets

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (statusDropdownRef.current && !statusDropdownRef.current.contains(event.target as Node)) {
        setStatusDropdownOpen(false)
      }
      if (ownerDropdownRef.current && !ownerDropdownRef.current.contains(event.target as Node)) {
        setOwnerDropdownOpen(false)
        setOwnerSearchQuery('')
      }
      if (locationDropdownRef.current && !locationDropdownRef.current.contains(event.target as Node)) {
        setLocationDropdownOpen(false)
      }
      if (classificationDropdownRef.current && !classificationDropdownRef.current.contains(event.target as Node)) {
        setClassificationDropdownOpen(false)
      }
      if (domainDropdownRef.current && !domainDropdownRef.current.contains(event.target as Node)) {
        setDomainDropdownOpen(false)
      }
      if (tagDropdownRef.current && !tagDropdownRef.current.contains(event.target as Node)) {
        setTagDropdownOpen(false)
      }
      if (datasetDropdownRef.current && !datasetDropdownRef.current.contains(event.target as Node)) {
        setDatasetDropdownOpen(false)
        setDatasetSearchQuery('')
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

  const toggleSelectAll = () => {
    if (selectedIds.size === sortedDatasets.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(sortedDatasets.map(d => d.id)))
    }
  }

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleBulkTags = async () => {
    const tags = bulkTagInput.split(',').map(t => t.trim()).filter(Boolean)
    if (tags.length === 0 || selectedIds.size === 0) return
    try {
      await bulkUpdateTags({
        dataset_ids: Array.from(selectedIds),
        tags,
        mode: bulkTagMode,
      })
      setBulkTagInput('')
      setBulkActionType(null)
      setSelectedIds(new Set())
      fetchDatasets()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Bulk tag update failed')
    }
  }

  const handleBulkClassification = async () => {
    if (selectedIds.size === 0) return
    try {
      await bulkUpdateClassification({
        dataset_ids: Array.from(selectedIds),
        classification: bulkClassification || null,
        domain: bulkDomain || null,
      })
      setBulkClassification('')
      setBulkDomain('')
      setBulkActionType(null)
      setSelectedIds(new Set())
      fetchDatasets()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Bulk classification update failed')
    }
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
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
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
                        {facets?.status[status] != null && <span className="text-gray-400 ml-1">({facets.status[status]})</span>}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Owner Filter */}
          <div className="relative" ref={ownerDropdownRef}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Owner
            </label>
            <button
              type="button"
              onClick={() => setOwnerDropdownOpen(!ownerDropdownOpen)}
              className="w-full px-3 py-2 text-left border border-gray-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 flex items-center justify-between"
            >
              <span className="text-sm text-gray-700">
                {ownerFilter.length === 0
                  ? 'All'
                  : ownerFilter.length === 1
                  ? ownerFilter[0]
                  : `${ownerFilter.length} selected`}
              </span>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${ownerDropdownOpen ? 'transform rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {ownerDropdownOpen && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                <div className="p-2 border-b border-gray-200">
            <input
              type="text"
                    value={ownerSearchQuery}
                    onChange={(e) => setOwnerSearchQuery(e.target.value)}
                    placeholder="Search owners..."
                    className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
                <div className="py-1">
                  <label className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={ownerFilter.length === 0}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setOwnerFilter([])
                        }
                      }}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">All</span>
                  </label>
                  {filteredOwners.length === 0 ? (
                    <div className="px-3 py-2 text-sm text-gray-500">No owners found</div>
                  ) : (
                    filteredOwners.map((owner) => (
                      <label key={owner} className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={ownerFilter.includes(owner)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setOwnerFilter([...ownerFilter, owner])
                            } else {
                              setOwnerFilter(ownerFilter.filter(o => o !== owner))
                            }
                          }}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">{owner}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Location Filter */}
          <div className="relative" ref={locationDropdownRef}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location
            </label>
            <button
              type="button"
              onClick={() => setLocationDropdownOpen(!locationDropdownOpen)}
              className="w-full px-3 py-2 text-left border border-gray-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 flex items-center justify-between"
            >
              <span className="text-sm text-gray-700">
                {locationFilter.length === 0
                  ? 'All'
                  : locationFilter.length === 1
                  ? getLocationLabel(locationFilter[0])
                  : `${locationFilter.length} selected`}
              </span>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${locationDropdownOpen ? 'transform rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {locationDropdownOpen && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                <div className="py-1">
                  <label className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={locationFilter.length === 0}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setLocationFilter([])
                        }
                      }}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">All</span>
                  </label>
                  {uniqueLocationTypes.map((locationType) => (
                    <label key={locationType} className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={locationFilter.includes(locationType)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setLocationFilter([...locationFilter, locationType])
                          } else {
                            setLocationFilter(locationFilter.filter(l => l !== locationType))
                          }
                        }}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">{getLocationLabel(locationType)}{facets?.location_type[locationType] != null && <span className="text-gray-400 ml-1">({facets.location_type[locationType]})</span>}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Classification Filter */}
          <div className="relative" ref={classificationDropdownRef}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Classification
            </label>
            <button
              type="button"
              onClick={() => setClassificationDropdownOpen(!classificationDropdownOpen)}
              className="w-full px-3 py-2 text-left border border-gray-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 flex items-center justify-between"
            >
              <span className="text-sm text-gray-700">
                {classificationFilter.length === 0
                  ? 'All'
                  : classificationFilter.length === 1
                  ? getClassificationLabel(classificationFilter[0])
                  : `${classificationFilter.length} selected`}
              </span>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${classificationDropdownOpen ? 'transform rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {classificationDropdownOpen && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                <div className="py-1">
                  <label className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                    <input type="checkbox" checked={classificationFilter.length === 0} onChange={(e) => { if (e.target.checked) setClassificationFilter([]) }} className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                    <span className="ml-2 text-sm text-gray-700">All</span>
                  </label>
                  {['public', 'internal', 'confidential', 'restricted'].map((cls) => (
                    <label key={cls} className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                      <input type="checkbox" checked={classificationFilter.includes(cls)} onChange={(e) => { if (e.target.checked) setClassificationFilter([...classificationFilter, cls]); else setClassificationFilter(classificationFilter.filter(c => c !== cls)) }} className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                      <span className="ml-2 text-sm text-gray-700">{getClassificationLabel(cls)}{facets?.classification[cls] != null && <span className="text-gray-400 ml-1">({facets.classification[cls]})</span>}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Domain Filter */}
          <div className="relative" ref={domainDropdownRef}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Domain
            </label>
            <button
              type="button"
              onClick={() => setDomainDropdownOpen(!domainDropdownOpen)}
              className="w-full px-3 py-2 text-left border border-gray-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 flex items-center justify-between"
            >
              <span className="text-sm text-gray-700">
                {domainFilter.length === 0
                  ? 'All'
                  : domainFilter.length === 1
                  ? domainFilter[0]
                  : `${domainFilter.length} selected`}
              </span>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${domainDropdownOpen ? 'transform rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {domainDropdownOpen && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                <div className="py-1">
                  <label className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                    <input type="checkbox" checked={domainFilter.length === 0} onChange={(e) => { if (e.target.checked) setDomainFilter([]) }} className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                    <span className="ml-2 text-sm text-gray-700">All</span>
                  </label>
                  {uniqueDomains.map((d) => (
                    <label key={d} className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                      <input type="checkbox" checked={domainFilter.includes(d)} onChange={(e) => { if (e.target.checked) setDomainFilter([...domainFilter, d]); else setDomainFilter(domainFilter.filter(x => x !== d)) }} className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                      <span className="ml-2 text-sm text-gray-700">{d}{facets?.domain[d] != null && <span className="text-gray-400 ml-1">({facets.domain[d]})</span>}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Tag Filter */}
          <div className="relative" ref={tagDropdownRef}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tags
            </label>
            <button
              type="button"
              onClick={() => setTagDropdownOpen(!tagDropdownOpen)}
              className="w-full px-3 py-2 text-left border border-gray-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 flex items-center justify-between"
            >
              <span className="text-sm text-gray-700">
                {tagFilter.length === 0
                  ? 'All'
                  : tagFilter.length === 1
                  ? tagFilter[0]
                  : `${tagFilter.length} selected`}
              </span>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${tagDropdownOpen ? 'transform rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {tagDropdownOpen && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                <div className="py-1">
                  <label className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                    <input type="checkbox" checked={tagFilter.length === 0} onChange={(e) => { if (e.target.checked) setTagFilter([]) }} className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                    <span className="ml-2 text-sm text-gray-700">All</span>
                  </label>
                  {uniqueTags.map((t) => (
                    <label key={t} className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                      <input type="checkbox" checked={tagFilter.includes(t)} onChange={(e) => { if (e.target.checked) setTagFilter([...tagFilter, t]); else setTagFilter(tagFilter.filter(x => x !== t)) }} className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                      <span className="ml-2 text-sm text-gray-700">{t}{facets?.tags[t] != null && <span className="text-gray-400 ml-1">({facets.tags[t]})</span>}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Dataset Search */}
          <div className="relative" ref={datasetDropdownRef}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dataset
            </label>
            <button
              type="button"
              onClick={() => setDatasetDropdownOpen(!datasetDropdownOpen)}
              className="w-full px-3 py-2 text-left border border-gray-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 flex items-center justify-between"
            >
              <span className="text-sm text-gray-700">
                {datasetFilter.length === 0
                  ? 'All'
                  : datasetFilter.length === 1
                  ? datasetFilter[0]
                  : `${datasetFilter.length} selected`}
              </span>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${datasetDropdownOpen ? 'transform rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {datasetDropdownOpen && (
              <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                <div className="p-2 border-b border-gray-200">
                  <input
                    type="text"
                    value={datasetSearchQuery}
                    onChange={(e) => setDatasetSearchQuery(e.target.value)}
                    placeholder="Search datasets..."
                    className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
                <div className="py-1">
                  <label className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={datasetFilter.length === 0}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setDatasetFilter([])
                        }
                      }}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">All</span>
                  </label>
                  {filteredDatasets.length === 0 ? (
                    <div className="px-3 py-2 text-sm text-gray-500">No datasets found</div>
                  ) : (
                    filteredDatasets.map((dataset) => (
                      <label key={dataset} className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={datasetFilter.includes(dataset)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setDatasetFilter([...datasetFilter, dataset])
                            } else {
                              setDatasetFilter(datasetFilter.filter(d => d !== dataset))
                            }
                          }}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">{dataset}</span>
                      </label>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bulk Action Toolbar */}
      {selectedIds.size > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-blue-800">
              {selectedIds.size} dataset{selectedIds.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setBulkActionType('tags')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium ${
                  bulkActionType === 'tags' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-300 hover:bg-blue-50'
                }`}
              >
                Bulk Tags
              </button>
              <button
                onClick={() => setBulkActionType('classification')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium ${
                  bulkActionType === 'classification' ? 'bg-blue-600 text-white' : 'bg-white text-blue-700 border border-blue-300 hover:bg-blue-50'
                }`}
              >
                Bulk Classify
              </button>
              <button
                onClick={() => { setSelectedIds(new Set()); setBulkActionType(null) }}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800"
              >
                Clear
              </button>
            </div>
          </div>

          {bulkActionType === 'tags' && (
            <div className="flex items-center gap-3 mt-2">
              <select
                value={bulkTagMode}
                onChange={e => setBulkTagMode(e.target.value as 'add' | 'remove' | 'replace')}
                className="px-2 py-1.5 border border-gray-300 rounded-md text-sm"
              >
                <option value="add">Add tags</option>
                <option value="remove">Remove tags</option>
                <option value="replace">Replace all tags</option>
              </select>
              <input
                type="text"
                value={bulkTagInput}
                onChange={e => setBulkTagInput(e.target.value)}
                placeholder="tag1, tag2, tag3"
                className="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm"
              />
              <button
                onClick={handleBulkTags}
                className="px-4 py-1.5 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
              >
                Apply
              </button>
            </div>
          )}

          {bulkActionType === 'classification' && (
            <div className="flex items-center gap-3 mt-2">
              <select
                value={bulkClassification}
                onChange={e => setBulkClassification(e.target.value)}
                className="px-2 py-1.5 border border-gray-300 rounded-md text-sm"
              >
                <option value="">No classification</option>
                <option value="public">Public</option>
                <option value="internal">Internal</option>
                <option value="confidential">Confidential</option>
                <option value="restricted">Restricted</option>
              </select>
              <input
                type="text"
                value={bulkDomain}
                onChange={e => setBulkDomain(e.target.value)}
                placeholder="Domain (optional)"
                className="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm"
              />
              <button
                onClick={handleBulkClassification}
                className="px-4 py-1.5 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
              >
                Apply
              </button>
            </div>
          )}
        </div>
      )}

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
                  <th className="px-3 py-3 w-10">
                    <input
                      type="checkbox"
                      checked={selectedIds.size === sortedDatasets.length && sortedDatasets.length > 0}
                      onChange={toggleSelectAll}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </th>
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tags
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
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      No datasets found
                    </td>
                  </tr>
                ) : (
                  sortedDatasets.map((dataset) => (
                    <tr
                      key={dataset.id}
                      className="hover:bg-gray-50"
                    >
                      <td className="px-3 py-4">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(dataset.id)}
                          onChange={() => toggleSelect(dataset.id)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </td>
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
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {dataset.tags && dataset.tags.length > 0 ? (
                            dataset.tags.map((tag) => (
                              <span
                                key={tag}
                                className="inline-flex px-2 py-0.5 text-xs font-medium rounded-full bg-indigo-100 text-indigo-700"
                              >
                                {tag}
                              </span>
                            ))
                          ) : (
                            <span className="text-gray-400 text-xs italic">No tags</span>
                          )}
                        </div>
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

