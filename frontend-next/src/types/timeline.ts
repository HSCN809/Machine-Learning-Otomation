export interface TimelineScope {
    columns?: string[];
    rows?: number[];
    created_columns?: string[];
    removed_columns?: string[];
    renamed_columns?: Array<{ column?: string | null; new_name?: string | null }>;
    affects_row_order?: boolean;
}

export interface TimelineEvent {
    id: string;
    category: string;
    action: string | null;
    title: string | null;
    description: string | null;
    createdAt: Date;
    undoable: boolean;
    metadata: Record<string, unknown>;
    payload: Record<string, unknown>;
    step?: string | null;
    rollbackStatus: 'active' | 'reverted';
    replayable: boolean;
    revertedByEventId?: string | null;
    rollbackReason?: string | null;
    scope: TimelineScope;
}

export interface TimelineResponse {
    events: TimelineEvent[];
    canUndoLast: boolean;
    lastEventId?: string | null;
}

export interface TimelineRollbackEventSummary {
    id: string;
    category: string;
    action: string | null;
    title: string | null;
    description: string | null;
    step?: string | null;
    scope: TimelineScope;
}

export interface TimelineRollbackPlan {
    eventId: string;
    canRollback: boolean;
    targetEvent: TimelineRollbackEventSummary;
    dependentEvents: TimelineRollbackEventSummary[];
    preservedEvents: TimelineRollbackEventSummary[];
    invalidatedModelEvents: TimelineRollbackEventSummary[];
    unsupportedReplayEvents: TimelineRollbackEventSummary[];
}
