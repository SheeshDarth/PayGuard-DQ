'use client';

import { useEffect, useState } from 'react';
import { apiClient, Run } from '@/lib/api';
import Link from 'next/link';

export default function RunsPage() {
    const [runs, setRuns] = useState<Run[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadRuns();
    }, []);

    const loadRuns = async () => {
        try {
            const data = await apiClient.getRuns();
            setRuns(data.runs);
        } catch (error) {
            console.error('Failed to load runs:', error);
        } finally {
            setLoading(false);
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 90) return 'text-green-400';
        if (score >= 75) return 'text-yellow-400';
        if (score >= 60) return 'text-orange-400';
        return 'text-red-400';
    };

    const getScoreBg = (score: number) => {
        if (score >= 90) return 'bg-green-500/20 border-green-500/50';
        if (score >= 75) return 'bg-yellow-500/20 border-yellow-500/50';
        if (score >= 60) return 'bg-orange-500/20 border-orange-500/50';
        return 'bg-red-500/20 border-red-500/50';
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
            <div className="container mx-auto px-4 py-12">
                {/* Header */}
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-4xl font-bold text-white">All Runs</h1>
                    <Link
                        href="/"
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        ← New Upload
                    </Link>
                </div>

                {/* Runs List */}
                {loading ? (
                    <div className="text-center text-white text-xl">Loading...</div>
                ) : runs.length === 0 ? (
                    <div className="text-center text-white text-xl">No runs yet. Upload a dataset to get started!</div>
                ) : (
                    <div className="grid gap-6">
                        {runs.map((run) => (
                            <Link
                                key={run.run_id}
                                href={`/runs/${run.run_id}`}
                                className="block bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-200 transform hover:scale-[1.02]"
                            >
                                <div className="flex justify-between items-start">
                                    <div className="flex-1">
                                        <h2 className="text-2xl font-semibold text-white mb-2">
                                            {run.dataset_name}
                                        </h2>
                                        <div className="flex gap-6 text-sm text-blue-200">
                                            <span>📊 {run.row_count.toLocaleString()} rows</span>
                                            <span>📋 {run.column_count} columns</span>
                                            <span>🕐 {new Date(run.timestamp).toLocaleString()}</span>
                                        </div>
                                        <div className="mt-2">
                                            <span className="text-xs text-gray-400">Run ID: {run.run_id}</span>
                                        </div>
                                    </div>
                                    <div className={`px-6 py-4 rounded-lg border ${getScoreBg(run.composite_dqs || 0)}`}>
                                        <div className="text-sm text-white/70 mb-1">DQS</div>
                                        <div className={`text-3xl font-bold ${getScoreColor(run.composite_dqs || 0)}`}>
                                            {run.composite_dqs?.toFixed(1) || 'N/A'}
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
