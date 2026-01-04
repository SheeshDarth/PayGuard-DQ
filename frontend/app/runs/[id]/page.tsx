'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiClient, RunDetail } from '@/lib/api';
import Link from 'next/link';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#ec4899', '#06b6d4'];

export default function RunDetailPage() {
    const params = useParams();
    const runId = params.id as string;
    const [runDetail, setRunDetail] = useState<RunDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'issues' | 'actions' | 'logs'>('overview');

    useEffect(() => {
        if (runId) {
            loadRunDetail();
        }
    }, [runId]);

    const loadRunDetail = async () => {
        try {
            const data = await apiClient.getRun(runId);
            setRunDetail(data);
        } catch (error) {
            console.error('Failed to load run detail:', error);
        } finally {
            setLoading(false);
        }
    };

    const downloadFile = (blob: Blob, filename: string) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    const handleDownloadDbt = async () => {
        const blob = await apiClient.downloadDbt(runId);
        downloadFile(blob, `dbt_tests_${runId}.yml`);
    };

    const handleDownloadGE = async () => {
        const blob = await apiClient.downloadGE(runId);
        downloadFile(blob, `ge_suite_${runId}.json`);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
                <div className="text-white text-2xl">Loading...</div>
            </div>
        );
    }

    if (!runDetail) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
                <div className="text-white text-2xl">Run not found</div>
            </div>
        );
    }

    const dimensionChartData = runDetail.scores.dimension_scores.map((ds) => ({
        name: ds.dimension,
        value: ds.score,
    }));

    const failingChecks = runDetail.checks.filter((c) => !c.passed);
    const criticalIssues = failingChecks.filter((c) => c.severity === 'critical');
    const highIssues = failingChecks.filter((c) => c.severity === 'high');

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
            <div className="container mx-auto px-4 py-12">
                {/* Header */}
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-4xl font-bold text-white mb-2">{runDetail.run.dataset_name}</h1>
                        <p className="text-blue-200">Run ID: {runDetail.run.run_id}</p>
                    </div>
                    <Link
                        href="/runs"
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        ← All Runs
                    </Link>
                </div>

                {/* Score Card */}
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 mb-8 shadow-2xl">
                    <div className="flex justify-between items-center">
                        <div>
                            <h2 className="text-white/80 text-lg mb-2">Overall Data Quality Score</h2>
                            <div className="text-6xl font-bold text-white">{runDetail.scores.composite_dqs.toFixed(1)}</div>
                            <div className="text-white/80 mt-2">
                                {runDetail.run.row_count.toLocaleString()} rows × {runDetail.run.column_count} columns
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-white/80 text-sm mb-2">Issues</div>
                            <div className="space-y-1">
                                {criticalIssues.length > 0 && (
                                    <div className="text-red-300">🔴 {criticalIssues.length} Critical</div>
                                )}
                                {highIssues.length > 0 && (
                                    <div className="text-orange-300">🟠 {highIssues.length} High</div>
                                )}
                                {failingChecks.length === 0 && (
                                    <div className="text-green-300">✅ No Issues</div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6">
                    {(['overview', 'issues', 'actions', 'logs'] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-6 py-3 rounded-lg font-semibold transition-colors ${activeTab === tab
                                    ? 'bg-white text-blue-900'
                                    : 'bg-white/10 text-white hover:bg-white/20'
                                }`}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
                    {activeTab === 'overview' && (
                        <div>
                            <h2 className="text-2xl font-bold text-white mb-6">Dimension Scores</h2>
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                <div>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <PieChart>
                                            <Pie
                                                data={dimensionChartData}
                                                cx="50%"
                                                cy="50%"
                                                labelLine={false}
                                                label={(entry) => `${entry.name}: ${entry.value.toFixed(1)}`}
                                                outerRadius={100}
                                                fill="#8884d8"
                                                dataKey="value"
                                            >
                                                {dimensionChartData.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className="space-y-3">
                                    {runDetail.scores.dimension_scores.map((ds) => (
                                        <div key={ds.dimension} className="bg-white/5 rounded-lg p-4">
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="text-white font-semibold capitalize">{ds.dimension}</span>
                                                <span className="text-white font-bold">{ds.score.toFixed(1)}</span>
                                            </div>
                                            <div className="w-full bg-white/10 rounded-full h-2">
                                                <div
                                                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                                                    style={{ width: `${ds.score}%` }}
                                                />
                                            </div>
                                            <div className="text-xs text-blue-200 mt-1">Weight: {ds.weight.toFixed(2)}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Narrative */}
                            <div className="mt-8">
                                <h3 className="text-xl font-bold text-white mb-4">Executive Summary</h3>
                                <div className="bg-white/5 rounded-lg p-6 text-blue-100 whitespace-pre-wrap">
                                    {runDetail.narrative}
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'issues' && (
                        <div>
                            <h2 className="text-2xl font-bold text-white mb-6">Issues & Evidence</h2>
                            {failingChecks.length === 0 ? (
                                <div className="text-center text-green-300 text-xl py-12">
                                    ✅ No issues detected! All checks passed.
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {failingChecks.map((check, idx) => (
                                        <div key={idx} className="bg-white/5 rounded-lg p-6 border-l-4 border-red-500">
                                            <div className="flex justify-between items-start mb-3">
                                                <div>
                                                    <h3 className="text-lg font-semibold text-white">{check.check_id}</h3>
                                                    <div className="flex gap-3 mt-1">
                                                        <span className="text-sm text-blue-200 capitalize">Dimension: {check.dimension}</span>
                                                        <span className={`text-sm font-semibold ${check.severity === 'critical' ? 'text-red-400' :
                                                                check.severity === 'high' ? 'text-orange-400' :
                                                                    check.severity === 'medium' ? 'text-yellow-400' : 'text-blue-400'
                                                            }`}>
                                                            Severity: {check.severity.toUpperCase()}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="text-sm text-blue-100">
                                                <pre className="whitespace-pre-wrap">{JSON.stringify(check.metrics, null, 2)}</pre>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'actions' && (
                        <div>
                            <h2 className="text-2xl font-bold text-white mb-6">Actions & Exports</h2>

                            {/* Download Buttons */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                                <button
                                    onClick={handleDownloadDbt}
                                    className="px-6 py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg font-semibold hover:from-green-600 hover:to-emerald-700 transition-all"
                                >
                                    📥 Download dbt Tests
                                </button>
                                <button
                                    onClick={handleDownloadGE}
                                    className="px-6 py-4 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-pink-700 transition-all"
                                >
                                    📥 Download GE Suite
                                </button>
                            </div>

                            {/* Remediation Plan */}
                            {runDetail.remediation && (
                                <div>
                                    <h3 className="text-xl font-bold text-white mb-4">Remediation Plan</h3>
                                    <div className="space-y-4">
                                        {runDetail.remediation.remediation_plan && (
                                            <>
                                                {Object.entries(runDetail.remediation.remediation_plan).map(([phase, data]: [string, any]) => (
                                                    <div key={phase} className="bg-white/5 rounded-lg p-6">
                                                        <h4 className="text-lg font-semibold text-white mb-2">{phase.replace('_', ' ').toUpperCase()}</h4>
                                                        <div className="text-blue-200 text-sm space-y-1">
                                                            <div>Count: {data.count}</div>
                                                            <div>Expected Gain: +{data.expected_total_gain?.toFixed(1)} points</div>
                                                            <div>Timeline: {data.timeline}</div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'logs' && (
                        <div>
                            <h2 className="text-2xl font-bold text-white mb-6">Agent Execution Logs</h2>
                            <div className="space-y-4">
                                {runDetail.agent_logs.map((log, idx) => (
                                    <div key={idx} className="bg-white/5 rounded-lg p-6">
                                        <div className="flex justify-between items-start mb-3">
                                            <div>
                                                <h3 className="text-lg font-semibold text-white">
                                                    {log.step_order}. {log.agent_name}
                                                </h3>
                                                <div className="text-sm text-blue-200">
                                                    Duration: {log.duration_ms}ms
                                                </div>
                                            </div>
                                            <div className="text-xs text-gray-400">
                                                {new Date(log.timestamp).toLocaleTimeString()}
                                            </div>
                                        </div>
                                        <div className="text-sm text-blue-100">
                                            <div className="mb-2">
                                                <span className="font-semibold">Outputs:</span>
                                                <pre className="mt-1 whitespace-pre-wrap">{JSON.stringify(log.outputs, null, 2)}</pre>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
