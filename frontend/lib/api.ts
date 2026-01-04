/**
 * API client for backend communication.
 */
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface Run {
    run_id: string;
    dataset_name: string;
    row_count: number;
    column_count: number;
    timestamp: string;
    status: string;
    composite_dqs: number;
}

export interface RunDetail {
    run: Run & {
        dataset_fingerprint: string;
        error_message?: string;
    };
    scores: {
        composite_dqs: number;
        dimension_scores: Array<{
            dimension: string;
            score: number;
            weight: number;
            explainability: any;
        }>;
        dimension_weights: Record<string, number>;
    };
    checks: Array<{
        check_id: string;
        dimension: string;
        passed: boolean;
        severity: string;
        metrics: any;
    }>;
    narrative: string;
    remediation: any;
    agent_logs: Array<{
        agent_name: string;
        step_order: number;
        inputs: any;
        outputs: any;
        timestamp: string;
        duration_ms: number;
    }>;
}

export const apiClient = {
    async ingestDataset(file: File, datasetName?: string) {
        const formData = new FormData();
        formData.append('dataset_file', file);
        if (datasetName) {
            formData.append('dataset_name', datasetName);
        }

        const response = await api.post('/api/ingest', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    async ingestReference(file: File, referenceType: string) {
        const formData = new FormData();
        formData.append('reference_file', file);
        formData.append('reference_type', referenceType);

        const response = await api.post('/api/ingest-reference', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    async getRuns(): Promise<{ runs: Run[] }> {
        const response = await api.get('/api/runs');
        return response.data;
    },

    async getRun(runId: string): Promise<RunDetail> {
        const response = await api.get(`/api/runs/${runId}`);
        return response.data;
    },

    async downloadDbt(runId: string) {
        const response = await api.get(`/api/runs/${runId}/export/dbt`, {
            responseType: 'blob',
        });
        return response.data;
    },

    async downloadGE(runId: string) {
        const response = await api.get(`/api/runs/${runId}/export/ge`, {
            responseType: 'blob',
        });
        return response.data;
    },

    async getGovernanceReport(runId: string) {
        const response = await api.get(`/api/runs/${runId}/governance`);
        return response.data;
    },
};
