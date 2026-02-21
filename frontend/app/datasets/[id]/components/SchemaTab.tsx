'use client'

import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism'
import { DatasetDetail, generateProtobufSchema, generateScalaSchema, generatePythonSchema, getColumnLineage, ColumnLineageResponse } from '../../../api/client'

interface SchemaTabProps {
  dataset: DatasetDetail
}

export default function SchemaTab({ dataset }: SchemaTabProps) {
  const [generatingSchema, setGeneratingSchema] = useState<string | null>(null)
  const [generatedSchema, setGeneratedSchema] = useState<{ format: string; schema: string; test_code: string; dataset_name: string } | null>(null)
  const [activeSubTab, setActiveSubTab] = useState<'schema' | 'tests'>('schema')
  const [columnLineageMap, setColumnLineageMap] = useState<Record<string, ColumnLineageResponse>>({})
  const [loadingColumnLineage, setLoadingColumnLineage] = useState<Record<string, boolean>>({})

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Data Schema</h2>
          {dataset.columns && dataset.columns.length > 0 && (
            <div className="flex space-x-2">
              <button
                onClick={async () => {
                  setGeneratingSchema('protobuf')
                  setGeneratedSchema(null)
                  try {
                    const result = await generateProtobufSchema(dataset.id)
                    setGeneratedSchema(result)
                    setActiveSubTab('schema')
                  } catch (err) {
                    alert(err instanceof Error ? err.message : 'Failed to generate protobuf schema')
                  } finally {
                    setGeneratingSchema(null)
                  }
                }}
                disabled={generatingSchema !== null}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {generatingSchema === 'protobuf' ? 'Generating...' : 'Generate Protobuf'}
              </button>
              <button
                onClick={async () => {
                  setGeneratingSchema('scala')
                  setGeneratedSchema(null)
                  try {
                    const result = await generateScalaSchema(dataset.id)
                    setGeneratedSchema(result)
                    setActiveSubTab('schema')
                  } catch (err) {
                    alert(err instanceof Error ? err.message : 'Failed to generate Scala schema')
                  } finally {
                    setGeneratingSchema(null)
                  }
                }}
                disabled={generatingSchema !== null}
                className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                title="Generates Java classes (Scala-compatible)"
              >
                {generatingSchema === 'scala' ? 'Generating...' : 'Generate Java/Scala'}
              </button>
              <button
                onClick={async () => {
                  setGeneratingSchema('python')
                  setGeneratedSchema(null)
                  try {
                    const result = await generatePythonSchema(dataset.id)
                    setGeneratedSchema(result)
                    setActiveSubTab('schema')
                  } catch (err) {
                    alert(err instanceof Error ? err.message : 'Failed to generate Python schema')
                  } finally {
                    setGeneratingSchema(null)
                  }
                }}
                disabled={generatingSchema !== null}
                className="px-3 py-1.5 text-sm bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {generatingSchema === 'python' ? 'Generating...' : 'Generate Python'}
              </button>
            </div>
          )}
        </div>
        {dataset.columns && dataset.columns.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Column</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nullable</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lineage</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {dataset.columns.map((column) => {
                  const columnLineage = columnLineageMap[column.id]
                  const isLoadingColumnLineage = loadingColumnLineage[column.id]

                  return (
                    <tr key={column.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{column.name}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm text-gray-600">
                          {column.type || <span className="text-gray-400 italic">Unknown</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm text-gray-600">
                          {column.nullable === true ? (
                            <span className="text-orange-600">Yes</span>
                          ) : column.nullable === false ? (
                            <span className="text-green-600">No</span>
                          ) : (
                            <span className="text-gray-400 italic">Unknown</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-600">
                          {column.description || <span className="text-gray-400 italic">No description</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={async () => {
                            if (!columnLineage && !isLoadingColumnLineage) {
                              setLoadingColumnLineage(prev => ({ ...prev, [column.id]: true }))
                              try {
                                const lineage = await getColumnLineage(dataset.id, column.id)
                                setColumnLineageMap(prev => ({ ...prev, [column.id]: lineage }))
                              } catch (err) {
                                console.error('Failed to load column lineage:', err)
                                setColumnLineageMap(prev => ({ ...prev, [column.id]: { upstream: [], downstream: [] } }))
                              } finally {
                                setLoadingColumnLineage(prev => ({ ...prev, [column.id]: false }))
                              }
                            }
                          }}
                          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                        >
                          {isLoadingColumnLineage ? 'Loading...' : columnLineage ? 'View' : 'Show'}
                        </button>
                        {columnLineage && (
                          <div className="mt-2 p-2 bg-gray-50 rounded border border-gray-200 text-xs">
                            {columnLineage.upstream.length > 0 && (
                              <div className="mb-2">
                                <span className="font-medium text-gray-700">From: </span>
                                {columnLineage.upstream.map((item, idx) => (
                                  <span key={item.id}>
                                    {idx > 0 && ', '}
                                    <span className="text-blue-600">{item.upstream_column_name}</span>
                                    <span className="text-gray-500"> ({item.upstream_dataset_name})</span>
                                  </span>
                                ))}
                              </div>
                            )}
                            {columnLineage.downstream.length > 0 && (
                              <div>
                                <span className="font-medium text-gray-700">To: </span>
                                {columnLineage.downstream.map((item, idx) => (
                                  <span key={item.id}>
                                    {idx > 0 && ', '}
                                    <span className="text-green-600">{item.downstream_column_name}</span>
                                    <span className="text-gray-500"> ({item.downstream_dataset_name})</span>
                                  </span>
                                ))}
                              </div>
                            )}
                            {columnLineage.upstream.length === 0 && columnLineage.downstream.length === 0 && (
                              <span className="text-gray-500 italic">No lineage</span>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p className="text-sm">No schema information available</p>
            <p className="text-xs mt-1 text-gray-400">
              Schema will be populated when dataset is ingested with column metadata
            </p>
          </div>
        )}
      </div>

      {/* Generated Schema Display */}
      {generatedSchema && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Generated {generatedSchema.format === 'scala' ? 'Java (Scala-compatible)' : generatedSchema.format.charAt(0).toUpperCase() + generatedSchema.format.slice(1)} Schema
              </h3>
              {generatedSchema.format === 'scala' && (
                <p className="text-xs text-gray-500 mt-1">
                  Note: Avrotize generates Java classes which Scala can use directly
                </p>
              )}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => {
                  const content = activeSubTab === 'schema' ? generatedSchema.schema : generatedSchema.test_code
                  const blob = new Blob([content], { type: 'text/plain' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  let extension: string
                  let filename: string
                  if (generatedSchema.format === 'protobuf') {
                    extension = 'proto'
                    filename = `${generatedSchema.dataset_name.replace(/\s+/g, '_')}.${extension}`
                  } else if (generatedSchema.format === 'scala') {
                    extension = 'java'
                    filename = `${generatedSchema.dataset_name.replace(/\s+/g, '_')}${activeSubTab === 'tests' ? '_Test' : ''}.${extension}`
                  } else if (generatedSchema.format === 'python') {
                    extension = 'py'
                    filename = `${generatedSchema.dataset_name.replace(/\s+/g, '_')}${activeSubTab === 'tests' ? '_test' : ''}.${extension}`
                  } else {
                    extension = generatedSchema.format
                    filename = `${generatedSchema.dataset_name.replace(/\s+/g, '_')}${activeSubTab === 'tests' ? '_test' : ''}.${extension}`
                  }
                  a.href = url
                  a.download = filename
                  document.body.appendChild(a)
                  a.click()
                  document.body.removeChild(a)
                  URL.revokeObjectURL(url)
                }}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Download {activeSubTab === 'tests' ? 'Tests' : 'Schema'}
              </button>
              <button
                onClick={() => setGeneratedSchema(null)}
                className="px-3 py-1.5 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>

          {/* Subtabs for Schema and Tests */}
          {generatedSchema.test_code && (
            <div className="mb-4 border-b border-gray-200">
              <nav className="flex -mb-px" aria-label="Sub-tabs">
                <button
                  onClick={() => setActiveSubTab('schema')}
                  className={
                    'px-4 py-2 text-sm font-medium border-b-2 transition-colors ' +
                    (activeSubTab === 'schema'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300')
                  }
                >
                  Schema
                </button>
                <button
                  onClick={() => setActiveSubTab('tests')}
                  className={
                    'px-4 py-2 text-sm font-medium border-b-2 transition-colors ' +
                    (activeSubTab === 'tests'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300')
                  }
                >
                  Tests
                </button>
              </nav>
            </div>
          )}

          {/* Code Display */}
          <div className="rounded-md overflow-hidden border border-gray-200">
            <SyntaxHighlighter
              language={
                generatedSchema.format === 'protobuf' ? 'protobuf' :
                generatedSchema.format === 'scala' ? 'java' :
                generatedSchema.format === 'python' ? 'python' :
                'text'
              }
              style={vscDarkPlus}
              customStyle={{
                margin: 0,
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                lineHeight: '1.5',
                padding: '1rem',
              }}
              showLineNumbers={true}
              wrapLines={true}
              wrapLongLines={true}
              PreTag="div"
            >
              {activeSubTab === 'schema' ? generatedSchema.schema : (generatedSchema.test_code || 'No test code generated')}
            </SyntaxHighlighter>
          </div>
        </div>
      )}
    </div>
  )
}
