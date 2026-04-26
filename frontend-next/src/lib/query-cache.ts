import type { QueryClient, QueryKey } from '@tanstack/react-query';

const DATASET_QUERY_ROOTS = new Set([
    'dataset-timeline',
    'eda-summary',
    'eda-histogram',
    'eda-boxplot',
    'eda-category',
    'eda-scatter',
]);

function isDatasetQueryKey(queryKey: QueryKey): boolean {
    const root = queryKey[0];
    return typeof root === 'string' && DATASET_QUERY_ROOTS.has(root);
}

export const datasetQueryKeys = {
    timeline: (sessionId: string | null) => ['dataset-timeline', sessionId] as const,
    edaSummary: (sessionId: string | null) => ['eda-summary', sessionId] as const,
    edaHistogram: (sessionId: string | null, column: string | null) =>
        ['eda-histogram', sessionId, column] as const,
    edaBoxplot: (sessionId: string | null, column: string | null) =>
        ['eda-boxplot', sessionId, column] as const,
    edaCategory: (sessionId: string | null, column: string | null) =>
        ['eda-category', sessionId, column] as const,
    edaScatter: (sessionId: string | null, xColumn: string | null, yColumn: string | null) =>
        ['eda-scatter', sessionId, xColumn, yColumn] as const,
};

export async function invalidateDatasetQueries(queryClient: QueryClient): Promise<void> {
    await queryClient.invalidateQueries({
        predicate: (query) => isDatasetQueryKey(query.queryKey),
    });
}

export function clearDatasetQueries(queryClient: QueryClient): void {
    queryClient.removeQueries({
        predicate: (query) => isDatasetQueryKey(query.queryKey),
    });
}
