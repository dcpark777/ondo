'use client'

import { useCallback, useEffect, useState } from 'react'
import {
  DatasetDetail,
  QualityRule,
  QualityRuleExecution,
  listQualityRules,
  createQualityRule,
  deleteQualityRule,
  recordRuleExecution,
  getExecutionHistory,
  updateQualityRule,
} from '../../../api/client'

interface QualityTabProps {
  dataset: DatasetDetail
}

const RULE_TYPES = [
  { value: 'not_null', label: 'Not Null' },
  { value: 'unique', label: 'Unique' },
  { value: 'range', label: 'Range' },
  { value: 'regex', label: 'Regex' },
  { value: 'custom_sql', label: 'Custom SQL' },
  { value: 'accepted_values', label: 'Accepted Values' },
]

const SEVERITIES = [
  { value: 'error', label: 'Error', color: 'bg-red-100 text-red-800' },
  { value: 'warning', label: 'Warning', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'info', label: 'Info', color: 'bg-blue-100 text-blue-800' },
]

function getRuleTypeLabel(ruleType: string): string {
  return RULE_TYPES.find((rt) => rt.value === ruleType)?.label || ruleType
}

function getSeverityColor(severity: string): string {
  return SEVERITIES.find((s) => s.value === severity)?.color || 'bg-gray-100 text-gray-800'
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 30) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

export default function QualityTab({ dataset }: QualityTabProps) {
  const [rules, setRules] = useState<QualityRule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [expandedRuleId, setExpandedRuleId] = useState<string | null>(null)
  const [executionHistory, setExecutionHistory] = useState<Record<string, QualityRuleExecution[]>>({})
  const [loadingHistory, setLoadingHistory] = useState<string | null>(null)
  const [recordingRuleId, setRecordingRuleId] = useState<string | null>(null)

  // Add rule form state
  const [newRuleName, setNewRuleName] = useState('')
  const [newRuleType, setNewRuleType] = useState('not_null')
  const [newRuleColumn, setNewRuleColumn] = useState('')
  const [newRuleDescription, setNewRuleDescription] = useState('')
  const [newRuleParams, setNewRuleParams] = useState('')
  const [newRuleSeverity, setNewRuleSeverity] = useState('warning')
  const [submitting, setSubmitting] = useState(false)

  // Record result form state
  const [resultPassed, setResultPassed] = useState(true)
  const [resultRecordsChecked, setResultRecordsChecked] = useState('')
  const [resultRecordsFailed, setResultRecordsFailed] = useState('')
  const [resultErrorMessage, setResultErrorMessage] = useState('')

  const fetchRules = useCallback(async () => {
    try {
      setLoading(true)
      const data = await listQualityRules(dataset.id)
      setRules(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load quality rules')
    } finally {
      setLoading(false)
    }
  }, [dataset.id])

  useEffect(() => {
    fetchRules()
  }, [fetchRules])

  const handleAddRule = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      let parameters: Record<string, any> | undefined
      if (newRuleParams.trim()) {
        try {
          parameters = JSON.parse(newRuleParams)
        } catch {
          setError('Invalid JSON in parameters field')
          setSubmitting(false)
          return
        }
      }

      await createQualityRule(dataset.id, {
        name: newRuleName,
        rule_type: newRuleType,
        column_name: newRuleColumn || undefined,
        description: newRuleDescription || undefined,
        parameters,
        severity: newRuleSeverity,
      })

      // Reset form
      setNewRuleName('')
      setNewRuleType('not_null')
      setNewRuleColumn('')
      setNewRuleDescription('')
      setNewRuleParams('')
      setNewRuleSeverity('warning')
      setShowAddForm(false)
      await fetchRules()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create rule')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this rule?')) return
    try {
      await deleteQualityRule(dataset.id, ruleId)
      await fetchRules()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete rule')
    }
  }

  const handleToggleEnabled = async (rule: QualityRule) => {
    try {
      await updateQualityRule(dataset.id, rule.id, { enabled: !rule.enabled })
      await fetchRules()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update rule')
    }
  }

  const handleExpandRule = async (ruleId: string) => {
    if (expandedRuleId === ruleId) {
      setExpandedRuleId(null)
      return
    }
    setExpandedRuleId(ruleId)
    if (!executionHistory[ruleId]) {
      setLoadingHistory(ruleId)
      try {
        const history = await getExecutionHistory(dataset.id, ruleId)
        setExecutionHistory((prev) => ({ ...prev, [ruleId]: history }))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load history')
      } finally {
        setLoadingHistory(null)
      }
    }
  }

  const handleRecordResult = async (ruleId: string) => {
    try {
      await recordRuleExecution(dataset.id, ruleId, {
        passed: resultPassed,
        records_checked: resultRecordsChecked ? parseInt(resultRecordsChecked) : undefined,
        records_failed: resultRecordsFailed ? parseInt(resultRecordsFailed) : undefined,
        error_message: resultErrorMessage || undefined,
      })
      setRecordingRuleId(null)
      setResultPassed(true)
      setResultRecordsChecked('')
      setResultRecordsFailed('')
      setResultErrorMessage('')
      // Refresh rules and history
      await fetchRules()
      // Also refresh history if expanded
      if (expandedRuleId === ruleId) {
        const history = await getExecutionHistory(dataset.id, ruleId)
        setExecutionHistory((prev) => ({ ...prev, [ruleId]: history }))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record result')
    }
  }

  // Summary stats
  const enabledRules = rules.filter((r) => r.enabled)
  const rulesWithExecution = enabledRules.filter((r) => r.latest_execution)
  const passingRules = rulesWithExecution.filter((r) => r.latest_execution?.passed)
  const totalExecutions = rules.reduce((acc, r) => {
    const history = executionHistory[r.id]
    return acc + (history ? history.length : r.latest_execution ? 1 : 0)
  }, 0)

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          <span className="ml-3 text-gray-600">Loading quality rules...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <p className="text-red-800 text-sm">{error}</p>
            <button onClick={() => setError(null)} className="text-red-600 hover:text-red-800 text-sm">
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Summary */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Quality Rules Summary</h3>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            {showAddForm ? 'Cancel' : '+ Add Rule'}
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">{rules.length}</div>
            <div className="text-sm text-gray-600">Total Rules</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{passingRules.length}</div>
            <div className="text-sm text-gray-600">Passing</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-red-600">
              {rulesWithExecution.length - passingRules.length}
            </div>
            <div className="text-sm text-gray-600">Failing</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-gray-900">{totalExecutions}</div>
            <div className="text-sm text-gray-600">Total Executions</div>
          </div>
        </div>
        {rulesWithExecution.length > 0 && (
          <div className="mt-4">
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-200 rounded-full h-3">
                <div
                  className="bg-green-500 rounded-full h-3 transition-all"
                  style={{
                    width: `${(passingRules.length / rulesWithExecution.length) * 100}%`,
                  }}
                />
              </div>
              <span className="text-sm font-medium text-gray-700">
                {passingRules.length}/{rulesWithExecution.length} passing
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Add Rule Form */}
      {showAddForm && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Add Quality Rule</h3>
          <form onSubmit={handleAddRule} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rule Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newRuleName}
                  onChange={(e) => setNewRuleName(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., user_id must not be null"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rule Type <span className="text-red-500">*</span>
                </label>
                <select
                  value={newRuleType}
                  onChange={(e) => setNewRuleType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {RULE_TYPES.map((rt) => (
                    <option key={rt.value} value={rt.value}>
                      {rt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Column Name
                </label>
                <select
                  value={newRuleColumn}
                  onChange={(e) => setNewRuleColumn(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">-- Table-level rule --</option>
                  {dataset.columns.map((col) => (
                    <option key={col.id} value={col.name}>
                      {col.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Severity
                </label>
                <select
                  value={newRuleSeverity}
                  onChange={(e) => setNewRuleSeverity(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {SEVERITIES.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <input
                type="text"
                value={newRuleDescription}
                onChange={(e) => setNewRuleDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Optional description of what this rule checks"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Parameters (JSON)
              </label>
              <input
                type="text"
                value={newRuleParams}
                onChange={(e) => setNewRuleParams(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder='e.g., {"min": 0, "max": 100} for range, {"pattern": "^[A-Z]"} for regex'
              />
            </div>
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !newRuleName.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Creating...' : 'Create Rule'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Rules List */}
      {rules.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <div className="text-gray-400 text-4xl mb-3">&#9745;</div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">No quality rules defined</h3>
          <p className="text-sm text-gray-600">
            Add quality rules to track data quality checks for this dataset.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden"
            >
              {/* Rule Header */}
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {/* Pass/Fail Badge */}
                    {rule.latest_execution ? (
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          rule.latest_execution.passed
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {rule.latest_execution.passed ? 'PASS' : 'FAIL'}
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                        N/A
                      </span>
                    )}

                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className={`font-medium text-sm ${
                            rule.enabled ? 'text-gray-900' : 'text-gray-400 line-through'
                          }`}
                        >
                          {rule.name}
                        </span>
                        <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${getSeverityColor(rule.severity)}`}>
                          {rule.severity}
                        </span>
                        <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                          {getRuleTypeLabel(rule.rule_type)}
                        </span>
                        {rule.column_name && (
                          <span className="text-xs text-gray-500 font-mono">
                            {rule.column_name}
                          </span>
                        )}
                      </div>
                      {rule.description && (
                        <p className="text-xs text-gray-500 mt-0.5 truncate">{rule.description}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4 shrink-0">
                    {rule.latest_execution && (
                      <span className="text-xs text-gray-400">
                        {formatTimeAgo(rule.latest_execution.executed_at)}
                      </span>
                    )}
                    <button
                      onClick={() => setRecordingRuleId(recordingRuleId === rule.id ? null : rule.id)}
                      className="px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
                      title="Record Result"
                    >
                      Record
                    </button>
                    <button
                      onClick={() => handleToggleEnabled(rule)}
                      className={`px-2 py-1 text-xs font-medium rounded ${
                        rule.enabled
                          ? 'text-yellow-600 hover:text-yellow-800 hover:bg-yellow-50'
                          : 'text-green-600 hover:text-green-800 hover:bg-green-50'
                      }`}
                    >
                      {rule.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button
                      onClick={() => handleExpandRule(rule.id)}
                      className="px-2 py-1 text-xs font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded"
                    >
                      {expandedRuleId === rule.id ? 'Hide History' : 'History'}
                    </button>
                    <button
                      onClick={() => handleDeleteRule(rule.id)}
                      className="px-2 py-1 text-xs font-medium text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {/* Parameters display */}
                {rule.parameters && Object.keys(rule.parameters).length > 0 && (
                  <div className="mt-2 text-xs text-gray-500 font-mono bg-gray-50 rounded px-2 py-1 inline-block">
                    {JSON.stringify(rule.parameters)}
                  </div>
                )}
              </div>

              {/* Record Result Form */}
              {recordingRuleId === rule.id && (
                <div className="border-t border-gray-200 bg-gray-50 p-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Record Execution Result</h4>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Result</label>
                      <select
                        value={resultPassed ? 'pass' : 'fail'}
                        onChange={(e) => setResultPassed(e.target.value === 'pass')}
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                      >
                        <option value="pass">Pass</option>
                        <option value="fail">Fail</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Records Checked</label>
                      <input
                        type="number"
                        value={resultRecordsChecked}
                        onChange={(e) => setResultRecordsChecked(e.target.value)}
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                        placeholder="Optional"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Records Failed</label>
                      <input
                        type="number"
                        value={resultRecordsFailed}
                        onChange={(e) => setResultRecordsFailed(e.target.value)}
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                        placeholder="Optional"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Error Message</label>
                      <input
                        type="text"
                        value={resultErrorMessage}
                        onChange={(e) => setResultErrorMessage(e.target.value)}
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                        placeholder="Optional"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2 mt-3">
                    <button
                      onClick={() => setRecordingRuleId(null)}
                      className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleRecordResult(rule.id)}
                      className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
                    >
                      Submit
                    </button>
                  </div>
                </div>
              )}

              {/* Execution History */}
              {expandedRuleId === rule.id && (
                <div className="border-t border-gray-200 bg-gray-50 p-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Execution History</h4>
                  {loadingHistory === rule.id ? (
                    <div className="flex items-center text-sm text-gray-500">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2" />
                      Loading history...
                    </div>
                  ) : !executionHistory[rule.id] || executionHistory[rule.id].length === 0 ? (
                    <p className="text-sm text-gray-500">No execution history available.</p>
                  ) : (
                    <div className="space-y-1 max-h-64 overflow-y-auto">
                      <div className="grid grid-cols-5 gap-2 text-xs font-medium text-gray-500 uppercase tracking-wider pb-1 border-b border-gray-200">
                        <div>Status</div>
                        <div>Executed At</div>
                        <div>Checked</div>
                        <div>Failed</div>
                        <div>Error</div>
                      </div>
                      {executionHistory[rule.id].map((exec) => (
                        <div
                          key={exec.id}
                          className="grid grid-cols-5 gap-2 text-xs py-1.5 border-b border-gray-100"
                        >
                          <div>
                            <span
                              className={`inline-flex px-1.5 py-0.5 rounded text-xs font-medium ${
                                exec.passed
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-red-100 text-red-700'
                              }`}
                            >
                              {exec.passed ? 'PASS' : 'FAIL'}
                            </span>
                          </div>
                          <div className="text-gray-600">
                            {new Date(exec.executed_at).toLocaleString()}
                          </div>
                          <div className="text-gray-600">
                            {exec.records_checked != null ? exec.records_checked.toLocaleString() : '-'}
                          </div>
                          <div className={exec.records_failed ? 'text-red-600' : 'text-gray-600'}>
                            {exec.records_failed != null ? exec.records_failed.toLocaleString() : '-'}
                          </div>
                          <div className="text-gray-500 truncate" title={exec.error_message || ''}>
                            {exec.error_message || '-'}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
