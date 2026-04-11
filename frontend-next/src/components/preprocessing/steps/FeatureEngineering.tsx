'use client';

import { useMemo, useState } from 'react';
import { ColumnSelector } from '../ColumnSelector';
import { PreprocessingTabs } from '../PreprocessingTabs';
import {
    BinningStrategy,
    ColumnInfo,
    DatetimeFeaturePart,
    FeatureConfig,
    FeatureOperation,
    NumericFeatureOperation,
} from '@/types/preprocessing';
import { Loader2, Plus } from 'lucide-react';
import { theme } from '@/styles/theme';

interface FeatureEngineeringProps {
    columns: ColumnInfo[];
    numericColumns: ColumnInfo[];
    onApply: (config: FeatureConfig) => Promise<void>;
    isLoading: boolean;
}

type FeatureTab = 'numeric' | 'polynomial' | 'binning' | 'datetime' | 'categorical';

const FEATURE_TABS: { id: FeatureTab; label: string; icon: string; description: string }[] = [
    { id: 'numeric', label: 'Sayısal İşlem', icon: '🔢', description: 'Preset veya özel ifade ile yeni sütun üret.' },
    { id: 'polynomial', label: 'Polinom Özellik', icon: '📈', description: 'Seçilen sayısal sütunlar için x² oluştur.' },
    { id: 'binning', label: 'Binning', icon: '📊', description: 'Tek sütunu aralıklara bölerek kategorize et.' },
    { id: 'datetime', label: 'Tarih/Zaman', icon: '🕒', description: 'Tarih sütunlarından parçalar çıkar.' },
    { id: 'categorical', label: 'Kategorik Kombinasyon', icon: '🔗', description: 'Birden çok kategorik sütunu birleştir.' },
];

const NUMERIC_OPTIONS: { value: NumericFeatureOperation; label: string; description: string }[] = [
    { value: 'add', label: 'Toplama', description: '2 veya daha fazla sütunu topla.' },
    { value: 'subtract', label: 'Çıkarma', description: 'Tam 2 sütun arasında fark al.' },
    { value: 'multiply', label: 'Çarpma', description: '2 veya daha fazla sütunu çarp.' },
    { value: 'divide', label: 'Bölme', description: 'Tam 2 sütun arasında bölme yap.' },
    { value: 'custom', label: 'Özel İfade', description: 'Sütun isimleriyle formül yaz.' },
];

const BINNING_OPTIONS: { value: BinningStrategy; label: string; description: string }[] = [
    { value: 'equal_width', label: 'Equal Width', description: 'Aralık genişlikleri eşit olsun.' },
    { value: 'quantile', label: 'Quantile', description: 'Aralıklarda gözlem sayıları dengelensin.' },
];

const DATETIME_PARTS: { value: DatetimeFeaturePart; label: string }[] = [
    { value: 'year', label: 'Yıl' },
    { value: 'month', label: 'Ay' },
    { value: 'day', label: 'Gün' },
    { value: 'weekday', label: 'Haftanın Günü' },
    { value: 'hour', label: 'Saat' },
    { value: 'minute', label: 'Dakika' },
    { value: 'second', label: 'Saniye' },
];

const OPERATIONS = [
    { value: 'create_numeric', label: 'Sayısal İşlem', icon: '🔢', description: 'Matematiksel işlem uygula' },
    { value: 'polynomial', label: 'Polinom Özellik', icon: '📈', description: 'x², x³ gibi özellikler oluştur' },
    { value: 'binning', label: 'Binning', icon: '📊', description: 'Sayısal değeri kategorize et' },
];

export function FeatureEngineeringLegacy({ columns, numericColumns, onApply, isLoading }: FeatureEngineeringProps) {
    const [operation, setOperation] = useState<FeatureOperation>('create_numeric');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [newColumnName, setNewColumnName] = useState('');
    const [expression, setExpression] = useState('');

    const handleApply = async () => {
        if (selectedColumns.length === 0 || !newColumnName.trim()) return;

        await onApply({
            operation,
            sourceColumns: selectedColumns,
            newColumnName: newColumnName.trim(),
            expression: expression.trim() || undefined,
        });

        setSelectedColumns([]);
        setNewColumnName('');
        setExpression('');
    };

    const canApply = selectedColumns.length > 0 && newColumnName.trim();

    return (
        <div className="space-y-6">
            {/* Info */}
            <div
                className="p-4 rounded-xl border"
                style={{
                    borderColor: `${theme.colors.status.info}50`,
                    background: `${theme.colors.status.info}10`,
                }}
            >
                <p className="text-blue-400">
                    💡 Feature engineering ile yeni özellikler oluşturarak model performansını artırabilirsiniz.
                </p>
            </div>

            {/* Operation selector */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">İşlem Türü</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {OPERATIONS.map((op) => (
                        <button
                            key={op.value}
                            onClick={() => setOperation(op.value as FeatureOperation)}
                            disabled={isLoading}
                            className={`p-4 rounded-xl border text-left transition-all ${operation === op.value
                                    ? 'border-cyan-500/50 bg-cyan-500/10'
                                    : 'border-white/10 bg-white/5 hover:border-cyan-500/30'
                                }`}
                        >
                            <span className="text-xl">{op.icon}</span>
                            <p className="font-medium text-white mt-2">{op.label}</p>
                            <p className="text-xs text-gray-400 mt-1">{op.description}</p>
                        </button>
                    ))}
                </div>
            </div>

            {/* Column selector */}
            <ColumnSelector
                columns={operation === 'create_numeric' || operation === 'polynomial' ? numericColumns : columns}
                selectedColumns={selectedColumns}
                onChange={setSelectedColumns}
                label="Kaynak Sütunlar"
                disabled={isLoading}
            />

            {/* New column name */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Yeni Sütun Adı</label>
                <input
                    type="text"
                    value={newColumnName}
                    onChange={(e) => setNewColumnName(e.target.value)}
                    placeholder="örn: age_squared, salary_binned"
                    disabled={isLoading}
                    className="w-full px-4 py-2 rounded-lg border border-white/10 bg-white/5 text-white placeholder:text-gray-500 outline-none focus:border-cyan-500/50"
                />
            </div>

            {/* Expression for numeric operations */}
            {operation === 'create_numeric' && (
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">
                        İfade (opsiyonel)
                    </label>
                    <input
                        type="text"
                        value={expression}
                        onChange={(e) => setExpression(e.target.value)}
                        placeholder="örn: col1 + col2, col1 * 2"
                        disabled={isLoading}
                        className="w-full px-4 py-2 rounded-lg border border-white/10 bg-white/5 text-white placeholder:text-gray-500 outline-none focus:border-cyan-500/50"
                    />
                    <p className="text-xs text-gray-500">
                        Sütun adlarını kullanarak matematiksel ifade yazın.
                    </p>
                </div>
            )}

            {/* Apply button */}
            <button
                onClick={handleApply}
                disabled={!canApply || isLoading}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                    background: canApply && !isLoading ? theme.gradients.primary : 'rgba(255,255,255,0.1)',
                    boxShadow: canApply && !isLoading ? theme.glow.cyan : undefined,
                }}
            >
                {isLoading ? (
                    <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Oluşturuluyor...
                    </>
                ) : (
                    <>
                        <Plus className="w-5 h-5" />
                        Özellik Oluştur
                    </>
                )}
            </button>
        </div>
    );
}

export function FeatureEngineering({ columns, numericColumns, onApply, isLoading }: FeatureEngineeringProps) {
    const [activeTab, setActiveTab] = useState<FeatureTab>('numeric');

    const [numericOperation, setNumericOperation] = useState<NumericFeatureOperation>('add');
    const [numericColumnsSelected, setNumericColumnsSelected] = useState<string[]>([]);
    const [numericColumnName, setNumericColumnName] = useState('');
    const [numericExpression, setNumericExpression] = useState('');

    const [polynomialColumnsSelected, setPolynomialColumnsSelected] = useState<string[]>([]);

    const [binningColumn, setBinningColumn] = useState<string[]>([]);
    const [binningStrategy, setBinningStrategy] = useState<BinningStrategy>('equal_width');
    const [binCount, setBinCount] = useState('5');
    const [binningColumnName, setBinningColumnName] = useState('');

    const [datetimeColumn, setDatetimeColumn] = useState<string[]>([]);
    const [datetimePart, setDatetimePart] = useState<DatetimeFeaturePart>('year');
    const [datetimeColumnName, setDatetimeColumnName] = useState('');
    const [datetimeNameDirty, setDatetimeNameDirty] = useState(false);

    const [categoricalColumnsSelected, setCategoricalColumnsSelected] = useState<string[]>([]);
    const [categoricalColumnName, setCategoricalColumnName] = useState('');
    const [separator, setSeparator] = useState('_');

    const datetimeCandidateColumns = useMemo(
        () =>
            columns.filter((column) => {
                const dtype = column.dtype.toLowerCase();
                return column.type === 'datetime' || column.type === 'text' || dtype.includes('date') || dtype.includes('time');
            }),
        [columns]
    );

    const categoricalCandidateColumns = useMemo(
        () => columns.filter((column) => column.type === 'categorical' || column.type === 'text'),
        [columns]
    );

    const polynomialPreview = useMemo(
        () => polynomialColumnsSelected.map((column) => `${column}_squared`),
        [polynomialColumnsSelected]
    );

    const datetimeSuggestedName = datetimeColumn[0] ? `${datetimeColumn[0]}_${datetimePart}` : '';
    const effectiveDatetimeColumnName = datetimeNameDirty ? datetimeColumnName : datetimeSuggestedName;

    const numericCanApply = useMemo(() => {
        if (!numericColumnName.trim()) return false;
        if (numericOperation === 'custom') {
            return numericColumnsSelected.length > 0 && numericExpression.trim().length > 0;
        }
        if (numericOperation === 'subtract' || numericOperation === 'divide') {
            return numericColumnsSelected.length === 2;
        }
        return numericColumnsSelected.length >= 2;
    }, [numericColumnName, numericColumnsSelected, numericExpression, numericOperation]);

    const polynomialCanApply = polynomialColumnsSelected.length > 0;
    const binningCanApply = binningColumn.length === 1 && binningColumnName.trim().length > 0 && Number(binCount) >= 2;
    const datetimeCanApply = datetimeColumn.length === 1 && effectiveDatetimeColumnName.trim().length > 0;
    const categoricalCanApply = categoricalColumnsSelected.length >= 2 && categoricalColumnName.trim().length > 0;

    const canApply =
        (activeTab === 'numeric' && numericCanApply) ||
        (activeTab === 'polynomial' && polynomialCanApply) ||
        (activeTab === 'binning' && binningCanApply) ||
        (activeTab === 'datetime' && datetimeCanApply) ||
        (activeTab === 'categorical' && categoricalCanApply);

    const applyLabel =
        activeTab === 'polynomial'
            ? 'Polinom Özellikleri Oluştur'
            : activeTab === 'binning'
              ? 'Binning Uygula'
              : activeTab === 'datetime'
                ? 'Tarih Özelliği Oluştur'
                : activeTab === 'categorical'
                  ? 'Kombinasyon Oluştur'
                  : 'Özellik Oluştur';

    const handleApply = async () => {
        let config: FeatureConfig | null = null;

        if (activeTab === 'numeric' && numericCanApply) {
            config = {
                operation: 'create_numeric',
                sourceColumns: numericColumnsSelected,
                newColumnName: numericColumnName.trim(),
                expression: numericOperation === 'custom' ? numericExpression.trim() : undefined,
                params: { numericOperation },
            };
        } else if (activeTab === 'polynomial' && polynomialCanApply) {
            config = {
                operation: 'polynomial',
                sourceColumns: polynomialColumnsSelected,
            };
        } else if (activeTab === 'binning' && binningCanApply) {
            config = {
                operation: 'binning',
                sourceColumns: binningColumn,
                newColumnName: binningColumnName.trim(),
                params: {
                    strategy: binningStrategy,
                    binCount: Number(binCount),
                },
            };
        } else if (activeTab === 'datetime' && datetimeCanApply) {
            config = {
                operation: 'create_datetime',
                sourceColumns: datetimeColumn,
                newColumnName: effectiveDatetimeColumnName.trim(),
                params: { datetimePart },
            };
        } else if (activeTab === 'categorical' && categoricalCanApply) {
            config = {
                operation: 'create_categorical',
                sourceColumns: categoricalColumnsSelected,
                newColumnName: categoricalColumnName.trim(),
                params: { separator },
            };
        }

        if (!config) return;

        await onApply(config);

        if (activeTab === 'numeric') {
            setNumericOperation('add');
            setNumericColumnsSelected([]);
            setNumericColumnName('');
            setNumericExpression('');
        } else if (activeTab === 'polynomial') {
            setPolynomialColumnsSelected([]);
        } else if (activeTab === 'binning') {
            setBinningColumn([]);
            setBinningStrategy('equal_width');
            setBinCount('5');
            setBinningColumnName('');
        } else if (activeTab === 'datetime') {
            setDatetimeColumn([]);
            setDatetimePart('year');
            setDatetimeColumnName('');
            setDatetimeNameDirty(false);
        } else if (activeTab === 'categorical') {
            setCategoricalColumnsSelected([]);
            setCategoricalColumnName('');
            setSeparator('_');
        }
    };

    return (
        <div className="space-y-6">

            <PreprocessingTabs tabs={FEATURE_TABS} value={activeTab} onChange={setActiveTab} disabled={isLoading} />

            {activeTab === 'numeric' && (
                <div className="space-y-6">
                    <div className="space-y-3">
                        <label className="text-sm font-medium text-gray-300">İşlem Preseti</label>
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
                            {NUMERIC_OPTIONS.map((option) => {
                                const isSelected = numericOperation === option.value;
                                return (
                                    <button
                                        key={option.value}
                                        type="button"
                                        onClick={() => setNumericOperation(option.value)}
                                        disabled={isLoading}
                                        className={`rounded-xl border p-4 text-left transition-all ${
                                            isSelected
                                                ? 'border-cyan-500/60 bg-cyan-500/10 text-cyan-400'
                                                : 'border-white/10 bg-white/5 text-white hover:border-cyan-500/30 hover:bg-white/10'
                                        } ${isLoading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
                                    >
                                        <p className="font-medium">{option.label}</p>
                                        <p className="mt-1 text-xs text-gray-400">{option.description}</p>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    <ColumnSelector
                        columns={numericColumns}
                        selectedColumns={numericColumnsSelected}
                        onChange={setNumericColumnsSelected}
                        label="Kaynak Sayısal Sütunlar"
                        disabled={isLoading}
                    />

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300">Yeni Sütun Adı</label>
                        <input
                            type="text"
                            value={numericColumnName}
                            onChange={(e) => setNumericColumnName(e.target.value)}
                            placeholder="örn: total_score"
                            disabled={isLoading}
                            className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-white outline-none focus:border-cyan-500/50"
                        />
                    </div>

                    {numericOperation === 'custom' && (
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300">Özel İfade</label>
                            <input
                                type="text"
                                value={numericExpression}
                                onChange={(e) => setNumericExpression(e.target.value)}
                                placeholder="örn: col1 + col2 / 2"
                                disabled={isLoading}
                                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-white outline-none focus:border-cyan-500/50"
                            />
                            <p className="text-xs text-gray-500">
                                Yalnızca seçilen sütun adlarını ve temel aritmetik operatörleri kullanın.
                            </p>
                        </div>
                    )}
                </div>
            )}

            {activeTab === 'polynomial' && (
                <div className="space-y-6">
                    <ColumnSelector
                        columns={numericColumns}
                        selectedColumns={polynomialColumnsSelected}
                        onChange={setPolynomialColumnsSelected}
                        label="x² Oluşturulacak Sütunlar"
                        disabled={isLoading}
                    />

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300">Oluşacak Sütunlar</label>
                        <div className="flex flex-wrap gap-2 rounded-xl border border-white/10 bg-white/5 p-4">
                            {polynomialPreview.length > 0 ? (
                                polynomialPreview.map((item) => (
                                    <span key={item} className="rounded-full bg-cyan-500/10 px-3 py-1 text-sm text-cyan-400">
                                        {item}
                                    </span>
                                ))
                            ) : (
                                <p className="text-sm text-gray-500">Önizleme için en az bir sayısal sütun seçin.</p>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'binning' && (
                <div className="space-y-6">
                    <ColumnSelector
                        columns={numericColumns}
                        selectedColumns={binningColumn}
                        onChange={setBinningColumn}
                        label="Kaynak Sayısal Sütun"
                        multiSelect={false}
                        disabled={isLoading}
                    />

                    <div className="space-y-3">
                        <label className="text-sm font-medium text-gray-300">Binning Stratejisi</label>
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                            {BINNING_OPTIONS.map((option) => {
                                const isSelected = binningStrategy === option.value;
                                return (
                                    <button
                                        key={option.value}
                                        type="button"
                                        onClick={() => setBinningStrategy(option.value)}
                                        disabled={isLoading}
                                        className={`rounded-xl border p-4 text-left transition-all ${
                                            isSelected
                                                ? 'border-cyan-500/60 bg-cyan-500/10 text-cyan-400'
                                                : 'border-white/10 bg-white/5 text-white hover:border-cyan-500/30 hover:bg-white/10'
                                        } ${isLoading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
                                    >
                                        <p className="font-medium">{option.label}</p>
                                        <p className="mt-1 text-xs text-gray-400">{option.description}</p>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300">Yeni Sütun Adı</label>
                            <input
                                type="text"
                                value={binningColumnName}
                                onChange={(e) => setBinningColumnName(e.target.value)}
                                placeholder="örn: age_bucket"
                                disabled={isLoading}
                                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-white outline-none focus:border-cyan-500/50"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300">Aralık Sayısı</label>
                            <input
                                type="number"
                                min="2"
                                step="1"
                                value={binCount}
                                onChange={(e) => setBinCount(e.target.value)}
                                disabled={isLoading}
                                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-white outline-none focus:border-cyan-500/50"
                            />
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'datetime' && (
                <div className="space-y-6">
                    <ColumnSelector
                        columns={datetimeCandidateColumns}
                        selectedColumns={datetimeColumn}
                        onChange={setDatetimeColumn}
                        label="Kaynak Tarih/Zaman Sütunu"
                        multiSelect={false}
                        disabled={isLoading || datetimeCandidateColumns.length === 0}
                    />

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300">Çıkarılacak Parça</label>
                        <select
                            value={datetimePart}
                            onChange={(e) => setDatetimePart(e.target.value as DatetimeFeaturePart)}
                            disabled={isLoading}
                            className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-white outline-none focus:border-cyan-500/50"
                        >
                            {DATETIME_PARTS.map((part) => (
                                <option key={part.value} value={part.value} className="bg-gray-900">
                                    {part.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300">Yeni Sütun Adı</label>
                        <input
                            type="text"
                            value={effectiveDatetimeColumnName}
                            onChange={(e) => {
                                setDatetimeColumnName(e.target.value);
                                setDatetimeNameDirty(true);
                            }}
                            placeholder="örn: order_date_year"
                            disabled={isLoading}
                            className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-white outline-none focus:border-cyan-500/50"
                        />
                    </div>
                </div>
            )}

            {activeTab === 'categorical' && (
                <div className="space-y-6">
                    <ColumnSelector
                        columns={categoricalCandidateColumns}
                        selectedColumns={categoricalColumnsSelected}
                        onChange={setCategoricalColumnsSelected}
                        label="Birleştirilecek Sütunlar"
                        disabled={isLoading || categoricalCandidateColumns.length === 0}
                    />

                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300">Yeni Sütun Adı</label>
                            <input
                                type="text"
                                value={categoricalColumnName}
                                onChange={(e) => setCategoricalColumnName(e.target.value)}
                                placeholder="örn: city_segment"
                                disabled={isLoading}
                                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-white outline-none focus:border-cyan-500/50"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-300">Ayırıcı</label>
                            <input
                                type="text"
                                value={separator}
                                onChange={(e) => setSeparator(e.target.value || '_')}
                                placeholder="_"
                                disabled={isLoading}
                                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-white outline-none focus:border-cyan-500/50"
                            />
                        </div>
                    </div>
                </div>
            )}

            <button
                type="button"
                onClick={handleApply}
                disabled={!canApply || isLoading}
                className={`w-full flex items-center justify-center gap-2 rounded-xl px-6 py-3 font-medium text-white transition-all duration-200 ${
                    !canApply || isLoading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
                }`}
                style={{
                    background: canApply && !isLoading ? theme.gradients.primary : 'rgba(255,255,255,0.1)',
                    boxShadow: canApply && !isLoading ? theme.glow.cyan : undefined,
                }}
            >
                {isLoading ? (
                    <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        Oluşturuluyor...
                    </>
                ) : (
                    <>
                        <Plus className="h-5 w-5" />
                        {applyLabel}
                    </>
                )}
            </button>
        </div>
    );
}
