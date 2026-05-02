// Model Selection types

export type ProblemType = 'classification' | 'regression';

export type ModelCategory = 'linear' | 'tree' | 'svm' | 'ensemble';

export interface ModelInfo {
    id: string;
    name: string;
    category: ModelCategory;
    description: string;
    problemTypes: ProblemType[];
    icon: string;
    color: string;
    params: ModelParameter[];
}

export interface ModelParameter {
    name: string;
    label: string;
    type: 'number' | 'select' | 'boolean' | 'range';
    default: number | string | boolean;
    options?: { value: string | number; label: string }[];
    min?: number;
    max?: number;
    step?: number;
    description?: string;
}

export interface TrainingConfig {
    modelId: string;
    targetColumn: string;
    testSize: number;
    randomState: number;
    params: Record<string, unknown>;
}

export interface TrainingResult {
    modelId: string;
    modelName: string;
    metrics: ModelMetrics;
    confusionMatrix?: number[][];
    confusionLabels?: string[];
    featureImportance?: FeatureImportance[];
    trainingTime: number;
    timestamp: Date;
}

export interface SavedModelSummary {
    id: string;
    modelId: string;
    modelName: string;
    targetColumn: string;
    problemType: ProblemType;
    metrics: ModelMetrics;
    trainingTime: number | null;
    createdAt: string | null;
}

export interface ModelMetrics {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1Score?: number;
    auc?: number;
    mse?: number;
    rmse?: number;
    mae?: number;
    r2?: number;
}

export interface FeatureImportance {
    feature: string;
    importance: number;
}

export interface ConfusionMatrixData {
    matrix: number[][];
    labels: string[];
}

export interface ModelSelectionState {
    targetColumn: string | null;
    problemType: ProblemType | null;
    selectedModels: string[];
    trainingResults: TrainingResult[];
    isTraining: boolean;
    currentStep: number;
}

export const CLASSIFICATION_MODELS: ModelInfo[] = [
    {
        id: 'logistic_regression',
        name: 'Lojistik Regresyon',
        category: 'linear',
        description: 'İkili ve çoklu sınıflandırma için lineer model.',
        problemTypes: ['classification'],
        icon: '📈',
        color: '#4299e1',
        params: [
            { name: 'C', label: 'Düzenlileştirme (C)', type: 'number', default: 1.0, min: 0.01, max: 100, step: 0.1 },
            { name: 'max_iter', label: 'Maksimum İterasyon', type: 'number', default: 100, min: 50, max: 1000, step: 50 },
        ],
    },
    {
        id: 'random_forest_clf',
        name: 'Rastgele Orman',
        category: 'tree',
        description: 'Birden fazla karar ağacının ortalamasıyla çalışan sınıflandırma modeli.',
        problemTypes: ['classification'],
        icon: '🌲',
        color: '#48bb78',
        params: [
            { name: 'n_estimators', label: 'Ağaç Sayısı', type: 'number', default: 100, min: 10, max: 500, step: 10 },
            { name: 'max_depth', label: 'Maksimum Derinlik', type: 'number', default: 10, min: 1, max: 50, step: 1 },
        ],
    },
    {
        id: 'xgboost_clf',
        name: 'XGBoost',
        category: 'tree',
        description: 'Gradient boosting ile güçlü sınıflandırma performansı sunar.',
        problemTypes: ['classification'],
        icon: '🚀',
        color: '#ed8936',
        params: [
            { name: 'n_estimators', label: 'Ağaç Sayısı', type: 'number', default: 100, min: 10, max: 500, step: 10 },
            { name: 'learning_rate', label: 'Öğrenme Oranı', type: 'number', default: 0.1, min: 0.01, max: 1, step: 0.01 },
            { name: 'max_depth', label: 'Maksimum Derinlik', type: 'number', default: 6, min: 1, max: 20, step: 1 },
        ],
    },
    {
        id: 'svc',
        name: 'Destek Vektör Sınıflandırıcısı',
        category: 'svm',
        description: 'Yüksek boyutlu verilerde etkili sınıflandırma modeli.',
        problemTypes: ['classification'],
        icon: '🎯',
        color: '#9f7aea',
        params: [
            { name: 'C', label: 'Düzenlileştirme (C)', type: 'number', default: 1.0, min: 0.01, max: 100, step: 0.1 },
            {
                name: 'kernel',
                label: 'Çekirdek',
                type: 'select',
                default: 'rbf',
                options: [
                    { value: 'rbf', label: 'RBF' },
                    { value: 'linear', label: 'Doğrusal' },
                    { value: 'poly', label: 'Polinom' },
                ],
            },
        ],
    },
    {
        id: 'decision_tree_clf',
        name: 'Karar Ağacı',
        category: 'tree',
        description: 'Yorumlanabilir ağaç yapısıyla sınıflandırma yapar.',
        problemTypes: ['classification'],
        icon: '🌳',
        color: '#38a169',
        params: [
            { name: 'max_depth', label: 'Maksimum Derinlik', type: 'number', default: 10, min: 1, max: 50, step: 1 },
            { name: 'min_samples_split', label: 'Minimum Bölünme Örneği', type: 'number', default: 2, min: 2, max: 20, step: 1 },
        ],
    },
];

export const REGRESSION_MODELS: ModelInfo[] = [
    {
        id: 'linear_regression',
        name: 'Lineer Regresyon',
        category: 'linear',
        description: 'Basit ve yorumlanabilir doğrusal regresyon modeli.',
        problemTypes: ['regression'],
        icon: '📊',
        color: '#4299e1',
        params: [],
    },
    {
        id: 'ridge',
        name: 'Ridge Regresyon',
        category: 'linear',
        description: 'L2 düzenlileştirme ile çalışan doğrusal regresyon modeli.',
        problemTypes: ['regression'],
        icon: '📈',
        color: '#63b3ed',
        params: [
            { name: 'alpha', label: 'Alpha', type: 'number', default: 1.0, min: 0.01, max: 100, step: 0.1 },
        ],
    },
    {
        id: 'lasso',
        name: 'Lasso Regresyon',
        category: 'linear',
        description: 'L1 düzenlileştirme ile özellik seçimi yapabilen regresyon modeli.',
        problemTypes: ['regression'],
        icon: '🪢',
        color: '#38b2ac',
        params: [
            { name: 'alpha', label: 'Alpha', type: 'number', default: 1.0, min: 0.001, max: 100, step: 0.1 },
        ],
    },
    {
        id: 'random_forest_reg',
        name: 'Rastgele Orman Regresörü',
        category: 'tree',
        description: 'Topluluk ağaç yapısıyla regresyon tahmini yapar.',
        problemTypes: ['regression'],
        icon: '🌲',
        color: '#48bb78',
        params: [
            { name: 'n_estimators', label: 'Ağaç Sayısı', type: 'number', default: 100, min: 10, max: 500, step: 10 },
            { name: 'max_depth', label: 'Maksimum Derinlik', type: 'number', default: 10, min: 1, max: 50, step: 1 },
        ],
    },
    {
        id: 'xgboost_reg',
        name: 'XGBoost Regresörü',
        category: 'tree',
        description: 'Yüksek performanslı gradient boosting regresyon modeli.',
        problemTypes: ['regression'],
        icon: '🚀',
        color: '#ed8936',
        params: [
            { name: 'n_estimators', label: 'Ağaç Sayısı', type: 'number', default: 100, min: 10, max: 500, step: 10 },
            { name: 'learning_rate', label: 'Öğrenme Oranı', type: 'number', default: 0.1, min: 0.01, max: 1, step: 0.01 },
        ],
    },
    {
        id: 'svr',
        name: 'Destek Vektör Regresörü',
        category: 'svm',
        description: 'SVM tabanlı regresyon modeli.',
        problemTypes: ['regression'],
        icon: '🎯',
        color: '#9f7aea',
        params: [
            { name: 'C', label: 'Düzenlileştirme (C)', type: 'number', default: 1.0, min: 0.01, max: 100, step: 0.1 },
            {
                name: 'kernel',
                label: 'Çekirdek',
                type: 'select',
                default: 'rbf',
                options: [
                    { value: 'rbf', label: 'RBF' },
                    { value: 'linear', label: 'Doğrusal' },
                ],
            },
        ],
    },
];
