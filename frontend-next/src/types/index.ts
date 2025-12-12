// Common type definitions for ML Automation Platform

// Data types
export interface DataColumn {
    name: string;
    type: 'numeric' | 'categorical' | 'datetime' | 'text';
    uniqueCount: number;
    missingCount: number;
    missingPercentage: number;
}

export interface DatasetInfo {
    fileName: string;
    rows: number;
    columns: number;
    size: number; // bytes
    uploadedAt: string;
}

// Navigation types
export interface NavItem {
    id: string;
    label: string;
    icon: React.ReactNode;
    href: string;
    badge?: number;
}

// Step/Wizard types
export interface WizardStep {
    id: string;
    name: string;
    icon: string;
    status: 'pending' | 'current' | 'completed';
}

// LLM Suggestion types
export interface LLMSuggestion {
    id: string;
    type: string;
    title: string;
    description: string;
    priority: 'high' | 'medium' | 'low';
    action: () => void;
}

// Chart/Visualization types
export interface ChartData {
    labels: string[];
    datasets: Array<{
        label: string;
        data: number[];
        backgroundColor?: string | string[];
        borderColor?: string;
    }>;
}

// Modal/Dialog types
export interface ModalState {
    isOpen: boolean;
    title: string;
    content: React.ReactNode;
}

// Toast/Notification types
export interface Toast {
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message?: string;
    duration?: number;
}
