'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  GlossaryTerm,
  listGlossaryTerms,
  createGlossaryTerm,
  updateGlossaryTerm,
  deleteGlossaryTerm,
} from '../api/client'

export default function GlossaryPage() {
  const [terms, setTerms] = useState<GlossaryTerm[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterDomain, setFilterDomain] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingTerm, setEditingTerm] = useState<GlossaryTerm | null>(null)

  // Form state
  const [formName, setFormName] = useState('')
  const [formDefinition, setFormDefinition] = useState('')
  const [formDomain, setFormDomain] = useState('')
  const [formOwner, setFormOwner] = useState('')
  const [formStatus, setFormStatus] = useState('draft')

  const fetchTerms = async () => {
    try {
      const data = await listGlossaryTerms({
        q: searchQuery || undefined,
        domain: filterDomain || undefined,
        status: filterStatus || undefined,
      })
      setTerms(data)
    } catch (err) {
      console.error('Failed to fetch glossary terms:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTerms()
  }, [searchQuery, filterDomain, filterStatus])

  const resetForm = () => {
    setFormName('')
    setFormDefinition('')
    setFormDomain('')
    setFormOwner('')
    setFormStatus('draft')
    setShowCreateForm(false)
    setEditingTerm(null)
  }

  const handleCreate = async () => {
    if (!formName.trim() || !formDefinition.trim()) return
    try {
      await createGlossaryTerm({
        name: formName.trim(),
        definition: formDefinition.trim(),
        domain: formDomain.trim() || undefined,
        owner: formOwner.trim() || undefined,
        status: formStatus,
      })
      resetForm()
      fetchTerms()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create term')
    }
  }

  const handleUpdate = async () => {
    if (!editingTerm || !formName.trim() || !formDefinition.trim()) return
    try {
      await updateGlossaryTerm(editingTerm.id, {
        name: formName.trim(),
        definition: formDefinition.trim(),
        domain: formDomain.trim() || undefined,
        owner: formOwner.trim() || undefined,
        status: formStatus,
      })
      resetForm()
      fetchTerms()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update term')
    }
  }

  const handleDelete = async (termId: string) => {
    if (!confirm('Delete this glossary term?')) return
    try {
      await deleteGlossaryTerm(termId)
      fetchTerms()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete term')
    }
  }

  const startEditing = (term: GlossaryTerm) => {
    setEditingTerm(term)
    setFormName(term.name)
    setFormDefinition(term.definition)
    setFormDomain(term.domain || '')
    setFormOwner(term.owner || '')
    setFormStatus(term.status)
    setShowCreateForm(true)
  }

  const domains = Array.from(new Set(terms.map((t) => t.domain).filter((d): d is string => Boolean(d))))

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800'
      case 'deprecated':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-yellow-100 text-yellow-800'
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Business Glossary</h1>
          <p className="text-sm text-gray-500 mt-1">
            Define business terms and link them to dataset columns
          </p>
        </div>
        <button
          onClick={() => {
            resetForm()
            setShowCreateForm(true)
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
        >
          Add Term
        </button>
      </div>

      {/* Search and filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Search terms..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filterDomain}
            onChange={(e) => setFilterDomain(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Domains</option>
            {domains.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="approved">Approved</option>
            <option value="deprecated">Deprecated</option>
          </select>
        </div>
      </div>

      {/* Create/Edit Form */}
      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            {editingTerm ? 'Edit Term' : 'New Term'}
          </h3>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Customer Lifetime Value"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Domain
                </label>
                <input
                  type="text"
                  value={formDomain}
                  onChange={(e) => setFormDomain(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., analytics"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Definition *
              </label>
              <textarea
                value={formDefinition}
                onChange={(e) => setFormDefinition(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Define this business term..."
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Owner
                </label>
                <input
                  type="text"
                  value={formOwner}
                  onChange={(e) => setFormOwner(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Data Team"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={formStatus}
                  onChange={(e) => setFormStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="draft">Draft</option>
                  <option value="approved">Approved</option>
                  <option value="deprecated">Deprecated</option>
                </select>
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={editingTerm ? handleUpdate : handleCreate}
                disabled={!formName.trim() || !formDefinition.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium"
              >
                {editingTerm ? 'Update' : 'Create'}
              </button>
              <button
                onClick={resetForm}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 text-sm font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Terms list */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading glossary...</div>
      ) : terms.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow-sm border border-gray-200">
          <p className="text-gray-500">No glossary terms found</p>
          <p className="text-sm text-gray-400 mt-1">
            Create your first term to start building the business glossary
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {terms.map((term) => (
            <div
              key={term.id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-5"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {term.name}
                    </h3>
                    <span
                      className={
                        'inline-flex px-2 py-0.5 text-xs font-medium rounded-full ' +
                        getStatusBadge(term.status)
                      }
                    >
                      {term.status}
                    </span>
                    {term.domain && (
                      <span className="inline-flex px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                        {term.domain}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{term.definition}</p>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    {term.owner && <span>Owner: {term.owner}</span>}
                    <span>
                      {term.linked_columns_count} linked column
                      {term.linked_columns_count !== 1 ? 's' : ''}
                    </span>
                    <span>
                      Updated:{' '}
                      {new Date(term.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                  {term.linked_columns && term.linked_columns.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {term.linked_columns.map((col) => (
                        <Link
                          key={col.link_id}
                          href={`/datasets/${col.dataset_id}?tab=schema`}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-xs text-gray-700 hover:bg-gray-200"
                        >
                          <span className="font-medium">{col.column_name}</span>
                          <span className="text-gray-400">
                            ({col.dataset_name})
                          </span>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex space-x-2 ml-4">
                  <button
                    onClick={() => startEditing(term)}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(term.id)}
                    className="text-xs text-red-600 hover:text-red-800 font-medium"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
