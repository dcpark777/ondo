'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  DatasetDetail,
  getColumnLineage,
  getLineageGraph,
  getImpactAnalysis,
  ColumnLineageResponse,
  LineageGraph,
  LineageGraphNode,
  ImpactAnalysis,
} from '../../../api/client'

interface LineageTabProps {
  dataset: DatasetDetail
}

/**
 * Layout algorithm for the lineage graph.
 * Assigns layers via BFS from the root node (upstream = negative, downstream = positive),
 * then positions nodes in columns by layer.
 */
function layoutGraph(graph: LineageGraph) {
  const layers: Record<string, number> = {}
  const adjacency: Record<string, string[]> = {} // target -> sources
  const reverseAdj: Record<string, string[]> = {} // source -> targets

  graph.edges.forEach(e => {
    if (!adjacency[e.target]) adjacency[e.target] = []
    adjacency[e.target].push(e.source)
    if (!reverseAdj[e.source]) reverseAdj[e.source] = []
    reverseAdj[e.source].push(e.target)
  })

  // BFS from root - upstream gets negative layers, downstream positive
  layers[graph.root_id] = 0

  // BFS upstream
  let queue = [graph.root_id]
  let visited = new Set([graph.root_id])
  while (queue.length > 0) {
    const current = queue.shift()!
    const sources = adjacency[current] || []
    for (const src of sources) {
      if (!visited.has(src)) {
        visited.add(src)
        layers[src] = (layers[current] ?? 0) - 1
        queue.push(src)
      }
    }
  }

  // BFS downstream
  queue = [graph.root_id]
  visited = new Set([graph.root_id])
  while (queue.length > 0) {
    const current = queue.shift()!
    const targets = reverseAdj[current] || []
    for (const tgt of targets) {
      if (!visited.has(tgt)) {
        visited.add(tgt)
        layers[tgt] = (layers[current] ?? 0) + 1
        queue.push(tgt)
      }
    }
  }

  // Any unassigned nodes
  graph.nodes.forEach(n => {
    if (layers[n.id] === undefined) layers[n.id] = 0
  })

  // Group nodes by layer
  const layerGroups: Record<number, LineageGraphNode[]> = {}
  graph.nodes.forEach(n => {
    const layer = layers[n.id]
    if (!layerGroups[layer]) layerGroups[layer] = []
    layerGroups[layer].push(n)
  })

  const NODE_W = 200
  const NODE_H = 80
  const H_GAP = 120
  const V_GAP = 30

  const sortedLayers = Object.keys(layerGroups).map(Number).sort((a, b) => a - b)
  const minLayer = sortedLayers[0] || 0

  const positions: Record<string, { x: number; y: number }> = {}

  sortedLayers.forEach(layer => {
    const nodes = layerGroups[layer]
    const col = layer - minLayer
    const x = col * (NODE_W + H_GAP) + 50
    const startY = 50
    nodes.forEach((node, idx) => {
      positions[node.id] = { x, y: startY + idx * (NODE_H + V_GAP) }
    })
  })

  // Calculate SVG dimensions
  const allPositions = Object.values(positions)
  const maxX = allPositions.length > 0 ? Math.max(...allPositions.map(p => p.x)) + NODE_W + 50 : 400
  const maxY = allPositions.length > 0 ? Math.max(...allPositions.map(p => p.y)) + NODE_H + 50 : 200

  return { positions, width: Math.max(maxX, 400), height: Math.max(maxY, 200), NODE_W, NODE_H }
}

export default function LineageTab({ dataset }: LineageTabProps) {
  const [columnLineageMap, setColumnLineageMap] = useState<Record<string, ColumnLineageResponse>>({})
  const [loadingColumnLineage, setLoadingColumnLineage] = useState<Record<string, boolean>>({})

  // Lineage graph state
  const [graph, setGraph] = useState<LineageGraph | null>(null)
  const [graphDepth, setGraphDepth] = useState(2)
  const [loadingGraph, setLoadingGraph] = useState(false)

  // Impact analysis state
  const [impact, setImpact] = useState<ImpactAnalysis | null>(null)
  const [loadingImpact, setLoadingImpact] = useState(false)
  const [showImpact, setShowImpact] = useState(false)

  // Load lineage graph
  useEffect(() => {
    setLoadingGraph(true)
    getLineageGraph(dataset.id, graphDepth)
      .then(setGraph)
      .catch(err => {
        console.error('Failed to load lineage graph:', err)
        setGraph({ nodes: [], edges: [], root_id: dataset.id })
      })
      .finally(() => setLoadingGraph(false))
  }, [dataset.id, graphDepth])

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

  const loadImpact = () => {
    setShowImpact(true)
    setLoadingImpact(true)
    getImpactAnalysis(dataset.id)
      .then(setImpact)
      .catch(err => console.error('Failed to load impact analysis:', err))
      .finally(() => setLoadingImpact(false))
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'gold': return '#059669'
      case 'production_ready': return '#10b981'
      case 'internal': return '#f59e0b'
      default: return '#ef4444'
    }
  }

  return (
    <div className="space-y-6">
      {/* Dataset Lineage Graph */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Dataset Lineage</h2>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Depth:</label>
            <select
              value={graphDepth}
              onChange={e => setGraphDepth(Number(e.target.value))}
              className="px-2 py-1 border border-gray-300 rounded text-sm"
            >
              {[1, 2, 3, 4, 5].map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
        </div>

        {loadingGraph ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading lineage graph...</p>
          </div>
        ) : graph && graph.nodes.length > 0 ? (
          (() => {
            const layout = layoutGraph(graph)
            const { positions, width, height, NODE_W, NODE_H } = layout

            return (
              <div className="overflow-auto border border-gray-200 rounded-lg bg-gray-50">
                <svg width={width} height={height} className="min-w-full">
                  <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
                      <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
                    </marker>
                  </defs>

                  {/* Edges */}
                  {graph.edges.map((edge, i) => {
                    const from = positions[edge.source]
                    const to = positions[edge.target]
                    if (!from || !to) return null
                    const x1 = from.x + NODE_W
                    const y1 = from.y + NODE_H / 2
                    const x2 = to.x
                    const y2 = to.y + NODE_H / 2
                    const cx1 = x1 + (x2 - x1) * 0.4
                    const cx2 = x1 + (x2 - x1) * 0.6
                    return (
                      <g key={`edge-${i}`}>
                        <path
                          d={`M ${x1} ${y1} C ${cx1} ${y1}, ${cx2} ${y2}, ${x2} ${y2}`}
                          fill="none"
                          stroke="#94a3b8"
                          strokeWidth="2"
                          markerEnd="url(#arrowhead)"
                        />
                        {edge.transformation_type && (
                          <text
                            x={(x1 + x2) / 2}
                            y={(y1 + y2) / 2 - 8}
                            textAnchor="middle"
                            className="fill-gray-400 text-[10px]"
                          >
                            {edge.transformation_type}
                          </text>
                        )}
                      </g>
                    )
                  })}

                  {/* Nodes */}
                  {graph.nodes.map(node => {
                    const pos = positions[node.id]
                    if (!pos) return null
                    const isCurrent = node.is_current
                    return (
                      <g key={node.id}>
                        <a href={`/datasets/${node.id}`}>
                          <rect
                            x={pos.x}
                            y={pos.y}
                            width={NODE_W}
                            height={NODE_H}
                            rx="8"
                            ry="8"
                            fill={isCurrent ? '#2563eb' : '#ffffff'}
                            stroke={isCurrent ? '#1d4ed8' : '#d1d5db'}
                            strokeWidth={isCurrent ? 3 : 1.5}
                            className="drop-shadow-sm"
                          />
                          {/* Status indicator bar */}
                          <rect
                            x={pos.x}
                            y={pos.y}
                            width="6"
                            height={NODE_H}
                            rx="8"
                            fill={getStatusColor(node.readiness_status)}
                          />
                          {/* Name */}
                          <text
                            x={pos.x + 16}
                            y={pos.y + 28}
                            className={`text-xs font-semibold ${isCurrent ? 'fill-white' : 'fill-gray-900'}`}
                          >
                            {node.display_name.length > 22 ? node.display_name.slice(0, 22) + '...' : node.display_name}
                          </text>
                          {/* Full name */}
                          <text
                            x={pos.x + 16}
                            y={pos.y + 44}
                            className={`text-[10px] ${isCurrent ? 'fill-blue-200' : 'fill-gray-400'}`}
                          >
                            {node.full_name.length > 28 ? node.full_name.slice(0, 28) + '...' : node.full_name}
                          </text>
                          {/* Score badge */}
                          <rect
                            x={pos.x + NODE_W - 44}
                            y={pos.y + 52}
                            width="34"
                            height="20"
                            rx="4"
                            fill={isCurrent ? 'rgba(255,255,255,0.2)' : '#f3f4f6'}
                          />
                          <text
                            x={pos.x + NODE_W - 27}
                            y={pos.y + 66}
                            textAnchor="middle"
                            className={`text-[11px] font-bold ${isCurrent ? 'fill-white' : 'fill-gray-700'}`}
                          >
                            {node.readiness_score}
                          </text>
                        </a>
                      </g>
                    )
                  })}
                </svg>
              </div>
            )
          })()
        ) : (
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

      {/* Impact Analysis */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Impact Analysis</h2>
          {!showImpact && (
            <button
              onClick={loadImpact}
              className="px-3 py-1.5 bg-orange-50 text-orange-700 border border-orange-200 rounded-md text-sm font-medium hover:bg-orange-100"
            >
              Analyze Impact
            </button>
          )}
        </div>

        {showImpact && (
          loadingImpact ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
              <p className="mt-4 text-gray-600">Analyzing downstream impact...</p>
            </div>
          ) : impact ? (
            <div>
              <div className="mb-4 p-3 bg-orange-50 rounded-lg">
                <span className="text-sm text-orange-800">
                  Changes to <strong>{impact.dataset_name}</strong> may affect <strong>{impact.total_impacted}</strong> downstream dataset{impact.total_impacted !== 1 ? 's' : ''}
                </span>
              </div>
              {impact.impacted.length > 0 ? (
                <div className="space-y-2">
                  {impact.impacted.map((item) => (
                    <div key={item.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                      <div className="flex items-center gap-3">
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-100 text-orange-700 text-xs font-bold">
                          {item.depth}
                        </span>
                        <div>
                          <Link href={`/datasets/${item.id}`} className="text-sm font-medium text-gray-900 hover:text-blue-600">
                            {item.display_name}
                          </Link>
                          <div className="text-xs text-gray-500">{item.path.join(' \u2192 ')}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-gray-700">{item.readiness_score}</span>
                        <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                          item.readiness_status === 'gold' ? 'bg-yellow-100 text-yellow-800' :
                          item.readiness_status === 'production_ready' ? 'bg-green-100 text-green-800' :
                          item.readiness_status === 'internal' ? 'bg-orange-100 text-orange-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {item.readiness_status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">No downstream datasets affected</p>
              )}
            </div>
          ) : null
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
                                    <span className="text-xs text-blue-600">{'\u2192'}</span>
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
                                      <span className="text-xs text-green-600">{'\u2192'}</span>
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
