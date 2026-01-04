'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';

export default function Home() {
    const router = useRouter();
    const [datasetFile, setDatasetFile] = useState<File | null>(null);
    const [datasetName, setDatasetName] = useState('');
    const [referenceFiles, setReferenceFiles] = useState<{
        bin_map?: File;
        currency_rules?: File;
        mcc_codes?: File;
        settlement_ledger?: File;
    }>({});
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleDatasetUpload = async () => {
        if (!datasetFile) {
            setError('Please select a dataset file');
            return;
        }

        setUploading(true);
        setError('');
        setSuccess('');

        try {
            // Upload reference files first
            for (const [type, file] of Object.entries(referenceFiles)) {
                if (file) {
                    await apiClient.ingestReference(file, type);
                }
            }

            // Upload dataset
            const result = await apiClient.ingestDataset(datasetFile, datasetName);
            setSuccess(`Dataset processed successfully! Run ID: ${result.run_id}`);

            // Navigate to run detail after 2 seconds
            setTimeout(() => {
                router.push(`/runs/${result.run_id}`);
            }, 2000);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
            <div className="container mx-auto px-4 py-12">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-5xl font-bold text-white mb-4">
                        Data Quality Scoring
                    </h1>
                    <p className="text-xl text-blue-200">
                        GenAI Agent for Universal, Dimension-Based Data Quality Scoring in Payments
                    </p>
                </div>

                {/* Main Card */}
                <div className="max-w-4xl mx-auto bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
                    <h2 className="text-3xl font-semibold text-white mb-6">Upload Dataset</h2>

                    {/* Dataset Upload */}
                    <div className="mb-8">
                        <label className="block text-white text-sm font-medium mb-2">
                            Dataset File (CSV) *
                        </label>
                        <input
                            type="file"
                            accept=".csv"
                            onChange={(e) => setDatasetFile(e.target.files?.[0] || null)}
                            className="w-full px-4 py-3 bg-white/20 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Dataset Name */}
                    <div className="mb-8">
                        <label className="block text-white text-sm font-medium mb-2">
                            Dataset Name (optional)
                        </label>
                        <input
                            type="text"
                            value={datasetName}
                            onChange={(e) => setDatasetName(e.target.value)}
                            placeholder="e.g., transactions_batch1"
                            className="w-full px-4 py-3 bg-white/20 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Reference Files */}
                    <div className="mb-8">
                        <h3 className="text-xl font-semibold text-white mb-4">Reference Data (optional)</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-white text-sm font-medium mb-2">BIN Map</label>
                                <input
                                    type="file"
                                    accept=".csv"
                                    onChange={(e) => setReferenceFiles({ ...referenceFiles, bin_map: e.target.files?.[0] })}
                                    className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-white text-sm font-medium mb-2">Currency Rules</label>
                                <input
                                    type="file"
                                    accept=".csv"
                                    onChange={(e) => setReferenceFiles({ ...referenceFiles, currency_rules: e.target.files?.[0] })}
                                    className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-white text-sm font-medium mb-2">MCC Codes</label>
                                <input
                                    type="file"
                                    accept=".csv"
                                    onChange={(e) => setReferenceFiles({ ...referenceFiles, mcc_codes: e.target.files?.[0] })}
                                    className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-white text-sm font-medium mb-2">Settlement Ledger</label>
                                <input
                                    type="file"
                                    accept=".csv"
                                    onChange={(e) => setReferenceFiles({ ...referenceFiles, settlement_ledger: e.target.files?.[0] })}
                                    className="w-full px-3 py-2 bg-white/20 border border-white/30 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Error/Success Messages */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200">
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="mb-6 p-4 bg-green-500/20 border border-green-500/50 rounded-lg text-green-200">
                            {success}
                        </div>
                    )}

                    {/* Upload Button */}
                    <button
                        onClick={handleDatasetUpload}
                        disabled={uploading || !datasetFile}
                        className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-lg shadow-lg hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105"
                    >
                        {uploading ? 'Processing...' : 'Upload & Process Dataset'}
                    </button>

                    {/* View Runs Link */}
                    <div className="mt-6 text-center">
                        <a
                            href="/runs"
                            className="text-blue-300 hover:text-blue-200 underline"
                        >
                            View All Runs →
                        </a>
                    </div>
                </div>

                {/* Info Cards */}
                <div className="max-w-4xl mx-auto mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                        <div className="text-3xl mb-2">🔍</div>
                        <h3 className="text-lg font-semibold text-white mb-2">7 Dimensions</h3>
                        <p className="text-sm text-blue-200">
                            Completeness, Uniqueness, Validity, Consistency, Timeliness, Integrity, Reconciliation
                        </p>
                    </div>
                    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                        <div className="text-3xl mb-2">🤖</div>
                        <h3 className="text-lg font-semibold text-white mb-2">7 Agents</h3>
                        <p className="text-sm text-blue-200">
                            Profiler, Dimension Selector, Check Executor, Scoring, Explainer, Remediation, Test Export
                        </p>
                    </div>
                    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                        <div className="text-3xl mb-2">🔒</div>
                        <h3 className="text-lg font-semibold text-white mb-2">No Raw Data</h3>
                        <p className="text-sm text-blue-200">
                            Metadata-only storage. Full compliance with data governance policies.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
