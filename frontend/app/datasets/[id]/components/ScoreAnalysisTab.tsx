'use client'

import { useState } from 'react'
import { DatasetDetail, ScoreHistory } from '../../../api/client'
import { getDimensionLabel, ACTION_KEY_TO_DIMENSION } from '../../../lib/dataset-utils'

interface ScoreAnalysisTabProps {
  dataset: DatasetDetail
  historyData: ScoreHistory[]
  maxScore: number
  minScore: number
}

export default function ScoreAnalysisTab({ dataset, historyData, maxScore, minScore }: ScoreAnalysisTabProps) {
  const [openDimensionDropdowns, setOpenDimensionDropdowns] = useState<Set<string>>(new Set())

  return (
    <div className="space-y-6">
      {/* Last Scored Info */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-1">Last Scored</h2>
            <p className="text-sm text-gray-500">
              {dataset.last_scored_at
                ? new Date(dataset.last_scored_at).toLocaleString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : 'Never'}
            </p>
          </div>
        </div>
      </div>

      {/* Dimension Breakdown */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Dimension Breakdown
        </h2>
        <div className="space-y-4">
          {dataset.dimension_scores.map((dim) => {
            const isOpen = openDimensionDropdowns.has(dim.dimension_key)

            const dimensionActions = dataset.actions.filter(a => {
              const actionDimension = ACTION_KEY_TO_DIMENSION[a.action_key]
              return actionDimension === dim.dimension_key
            })

            const hasImprovements = dimensionActions.length > 0

            return (
              <div key={dim.dimension_key} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium text-gray-700">
                    {getDimensionLabel(dim.dimension_key)}
                    {dim.measured === false && (
                      <span className="ml-2 text-xs text-amber-600 font-medium">
                        (Not measured yet)
                      </span>
                    )}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">
                      {dim.measured === false ? (
                        <span className="text-gray-400 italic">N/A</span>
                      ) : (
                        `${dim.points_awarded}/${dim.max_points}`
                      )}
                    </span>
                    {dim.measured && hasImprovements && (
                      <button
                        onClick={() => {
                          const newSet = new Set(openDimensionDropdowns)
                          if (isOpen) {
                            newSet.delete(dim.dimension_key)
                          } else {
                            newSet.add(dim.dimension_key)
                          }
                          setOpenDimensionDropdowns(newSet)
                        }}
                        className="ml-2 text-xs text-blue-600 hover:text-blue-800 font-medium"
                      >
                        {isOpen ? 'Hide' : 'Show'} improvements
                      </button>
                    )}
                  </div>
                </div>
                {dim.measured === false ? (
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div className="h-2 rounded-full bg-gray-300" style={{ width: '100%' }}></div>
                  </div>
                ) : (
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={'h-2 rounded-full ' + (
                        dim.percentage >= 80
                          ? 'bg-green-600'
                          : dim.percentage >= 50
                          ? 'bg-yellow-600'
                          : 'bg-red-600'
                      )}
                      style={{ width: dim.percentage + '%' }}
                    ></div>
                  </div>
                )}

                {/* Dropdown for improvements */}
                {isOpen && dim.measured && hasImprovements && (
                  <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
                    {dimensionActions.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                          Recommended Actions
                        </h4>
                        <div className="space-y-2">
                          {dimensionActions.map((action) => (
                            <div
                              key={action.id}
                              className="flex items-start space-x-3 p-2 bg-blue-50 rounded-md"
                            >
                              <span className="text-blue-600 font-semibold text-xs">+{action.points_gain}</span>
                              <div className="flex-1">
                                <p className="text-xs font-medium text-gray-900">{action.title}</p>
                                {action.description && (
                                  <p className="text-xs text-gray-600 mt-0.5">{action.description}</p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Reasons */}
      {dataset.reasons.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Why this score?
          </h2>
          <div className="space-y-3">
            {dataset.reasons.map((reason) => {
              const dimScore = dataset.dimension_scores.find(
                (d) => d.dimension_key === reason.dimension_key
              )
              if (dimScore && !dimScore.measured) {
                return null
              }
              return (
                <div
                  key={reason.id}
                  className="flex items-start space-x-3 p-3 bg-red-50 rounded-md"
                >
                  <span className="text-red-600 font-semibold">-{reason.points_lost}</span>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{reason.message}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {getDimensionLabel(reason.dimension_key)}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Improvement Checklist */}
      {dataset.actions.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Improvement Checklist
          </h2>
          <div className="space-y-3">
            {dataset.actions
              .map((action) => {
                const dimensionKey = ACTION_KEY_TO_DIMENSION[action.action_key]
                if (dimensionKey) {
                  const dimScore = dataset.dimension_scores.find(
                    (d) => d.dimension_key === dimensionKey
                  )
                  if (dimScore && !dimScore.measured) {
                    return null
                  }
                }
                return (
                  <div
                    key={action.id}
                    className="flex items-start space-x-3 p-3 bg-blue-50 rounded-md"
                  >
                    <span className="text-blue-600 font-semibold">+{action.points_gain}</span>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{action.title}</p>
                      <p className="text-xs text-gray-600 mt-1">{action.description}</p>
                    </div>
                  </div>
                )
              })
              .filter(Boolean)}
          </div>
        </div>
      )}

      {/* Score History */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Score History</h2>
        {historyData.length > 0 ? (
          <>
            <div className="h-64 flex items-end space-x-1">
              {historyData.map((entry) => {
                const height = ((entry.readiness_score - minScore) / (maxScore - minScore || 1)) * 100
                return (
                  <div
                    key={entry.id}
                    className="flex-1 bg-blue-600 rounded-t hover:bg-blue-700 transition cursor-pointer"
                    style={{ height: Math.max(height, 5) + '%' }}
                    title={entry.readiness_score + ' on ' + new Date(entry.recorded_at).toLocaleDateString()}
                  ></div>
                )
              })}
            </div>
            <div className="mt-4 flex justify-between text-xs text-gray-500">
              <span>
                {new Date(historyData[0].recorded_at).toLocaleDateString()}
              </span>
              <span>
                {new Date(historyData[historyData.length - 1].recorded_at).toLocaleDateString()}
              </span>
            </div>
          </>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p className="text-sm">No score history available</p>
          </div>
        )}
      </div>
    </div>
  )
}
