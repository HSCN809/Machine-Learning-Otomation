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
}

export interface TimelineResponse {
    events: TimelineEvent[];
    canUndoLast: boolean;
    lastEventId?: string | null;
}
