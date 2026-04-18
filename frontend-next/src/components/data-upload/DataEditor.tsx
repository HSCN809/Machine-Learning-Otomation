'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import {
    Eraser,
    RotateCcw,
    Save,
    Scissors,
    Trash2,
    XCircle,
} from 'lucide-react';
import { useDataEditor } from '@/hooks/useDataEditor';

interface DataEditorProps {
    onSaved?: () => Promise<void> | void;
    onDelete?: () => Promise<void> | void;
}

function getButtonClassName(disabled: boolean, tone: 'default' | 'danger' | 'primary' = 'default') {
    const toneClassName =
        tone === 'primary'
            ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/15'
            : tone === 'danger'
              ? 'border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/15'
              : 'border-white/10 bg-white/5 text-gray-200 hover:bg-white/10';

    return [
        'inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm transition-all',
        disabled ? 'cursor-not-allowed opacity-50' : `cursor-pointer ${toneClassName}`,
    ].join(' ');
}

function stringifyValue(value: unknown): string {
    if (value === null || value === undefined) {
        return '';
    }
    return String(value);
}

export function DataEditor({ onSaved, onDelete }: DataEditorProps) {
    const [isDeleting, setIsDeleting] = useState(false);
    const scrollContainerRef = useRef<HTMLDivElement | null>(null);
    const loadMoreRef = useRef<HTMLDivElement | null>(null);
    const {
        rows,
        columns,
        pageSize,
        totalRows,
        totalPages,
        loadedPages,
        hasMoreRows,
        error,
        isLoading,
        isLoadingMore,
        isSaving,
        draft,
        isDirty,
        selectedRows,
        selectedTrimColumns,
        activeCell,
        setActiveCell,
        loadMoreRows,
        toggleRowSelection,
        toggleAllLoadedRows,
        updateCell,
        clearActiveCell,
        deleteSelectedRows,
        toggleTrimColumnSelection,
        applyTrimSelection,
        removeTrimColumn,
        undoLastChange,
        discardChanges,
        saveChanges,
    } = useDataEditor({ onSaved });

    const handleDeleteDataset = async () => {
        if (!onDelete || isDeleting || isSaving) {
            return;
        }

        const confirmed = window.confirm(
            'Yuklenen veri seti silinecek ve bu oturumdaki duzenlemeler kaybolacak. Devam etmek istiyor musunuz?'
        );

        if (!confirmed) {
            return;
        }

        try {
            setIsDeleting(true);
            await onDelete();
        } finally {
            setIsDeleting(false);
        }
    };

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
                if (!isDirty || isSaving) {
                    return;
                }

                event.preventDefault();
                void saveChanges();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isDirty, isSaving, saveChanges]);

    useEffect(() => {
        const root = scrollContainerRef.current;
        const sentinel = loadMoreRef.current;

        if (!root || !sentinel || !hasMoreRows || isLoading || isLoadingMore || isSaving) {
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                const [entry] = entries;
                if (entry?.isIntersecting) {
                    void loadMoreRows();
                }
            },
            {
                root,
                rootMargin: '200px 0px',
                threshold: 0.1,
            }
        );

        observer.observe(sentinel);

        return () => {
            observer.disconnect();
        };
    }, [hasMoreRows, isLoading, isLoadingMore, isSaving, loadMoreRows]);

    const updatedCellMap = useMemo(
        () =>
            new Map<string, string>(
                draft.updatedCells.map((cell) => [`${cell.rowId}:${cell.column}`, cell.value])
            ),
        [draft.updatedCells]
    );
    const clearedCellSet = useMemo(
        () => new Set<string>(draft.clearedCells.map((cell) => `${cell.rowId}:${cell.column}`)),
        [draft.clearedCells]
    );
    const deletedRowSet = useMemo(() => new Set(draft.deletedRowIds), [draft.deletedRowIds]);
    const selectedRowSet = useMemo(() => new Set(selectedRows), [selectedRows]);
    const allRowsSelected = rows.length > 0 && rows.every((row) => selectedRowSet.has(row.rowId));

    if (isLoading && rows.length === 0) {
        return (
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-6 text-sm text-gray-400">
                Veri duzenleyici yukleniyor...
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-2">
                    <div>
                        <h2 className="text-xl font-semibold text-white">Veri Duzenleme</h2>
                        <p className="text-sm text-gray-400">
                            Veriler parcali olarak yuklenir. Kaydirdikca yeni satirlar gelir, degisiklikler yalnizca kaydettiginizde uygulanir.
                        </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400">
                        <span className="rounded-full border border-white/10 px-3 py-1">
                            Toplam satir: {totalRows}
                        </span>
                        <span className="rounded-full border border-white/10 px-3 py-1">
                            Yuklenen satir: {rows.length}
                        </span>
                        <span className="rounded-full border border-white/10 px-3 py-1">
                            Kaydedilmemis degisiklik: {isDirty ? 'Var' : 'Yok'}
                        </span>
                        <span className="rounded-full border border-white/10 px-3 py-1">
                            Ctrl+S ile kaydet
                        </span>
                    </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                    <button
                        type="button"
                        onClick={undoLastChange}
                        disabled={!isDirty || isSaving}
                        className={getButtonClassName(!isDirty || isSaving)}
                    >
                        <RotateCcw className="h-4 w-4" />
                        Geri Al
                    </button>
                    <button
                        type="button"
                        onClick={discardChanges}
                        disabled={!isDirty || isSaving}
                        className={getButtonClassName(!isDirty || isSaving)}
                    >
                        <XCircle className="h-4 w-4" />
                        Vazgec
                    </button>
                    <button
                        type="button"
                        onClick={() => {
                            void saveChanges();
                        }}
                        disabled={!isDirty || isSaving}
                        className={getButtonClassName(!isDirty || isSaving, 'primary')}
                    >
                        <Save className="h-4 w-4" />
                        {isSaving ? 'Kaydediliyor...' : 'Kaydet'}
                    </button>
                    <button
                        type="button"
                        onClick={() => {
                            void handleDeleteDataset();
                        }}
                        disabled={!onDelete || isDeleting || isSaving}
                        className={getButtonClassName(!onDelete || isDeleting || isSaving, 'danger')}
                    >
                        <Trash2 className="h-4 w-4" />
                        {isDeleting ? 'Siliniyor...' : 'Sil'}
                    </button>
                </div>
            </div>

            {error && (
                <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    {error}
                </div>
            )}

            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
                <div className="space-y-4">
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                        <div className="flex flex-wrap items-center gap-2 text-sm text-gray-300">
                            <span className="rounded-full border border-white/10 px-3 py-1">
                                Yuklenen bolum: {loadedPages} / {totalPages}
                            </span>
                            <span className="rounded-full border border-white/10 px-3 py-1">
                                Secili satir: {selectedRows.length}
                            </span>
                            <span className="rounded-full border border-white/10 px-3 py-1">
                                Silinecek satir: {draft.deletedRowIds.length}
                            </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                            <button
                                type="button"
                                onClick={clearActiveCell}
                                disabled={!activeCell || isSaving}
                                className={getButtonClassName(!activeCell || isSaving)}
                            >
                                <Eraser className="h-4 w-4" />
                                Secili Hucreyi Temizle
                            </button>
                            <button
                                type="button"
                                onClick={deleteSelectedRows}
                                disabled={selectedRows.length === 0 || isSaving}
                                className={getButtonClassName(selectedRows.length === 0 || isSaving, 'danger')}
                            >
                                <Trash2 className="h-4 w-4" />
                                Secili Satirlari Sil
                            </button>
                        </div>
                    </div>

                    <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/20">
                        <div ref={scrollContainerRef} className="max-h-[70vh] overflow-auto">
                            <table className="min-w-full text-sm">
                                <thead className="sticky top-0 z-10 bg-[#101827]">
                                    <tr className="border-b border-white/10">
                                        <th className="px-4 py-3 text-left">
                                            <input
                                                type="checkbox"
                                                checked={allRowsSelected}
                                                onChange={toggleAllLoadedRows}
                                                className="h-4 w-4 cursor-pointer rounded border-white/20 bg-transparent"
                                            />
                                        </th>
                                        <th className="px-4 py-3 text-left font-medium text-gray-400">#</th>
                                        {columns.map((column) => (
                                            <th
                                                key={column}
                                                className="px-4 py-3 text-left font-medium text-gray-400"
                                            >
                                                {column}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows.map((row) => {
                                        const isDeleted = deletedRowSet.has(row.rowId);

                                        return (
                                            <tr
                                                key={row.rowId}
                                                className={[
                                                    'border-b border-white/5 align-top transition-colors',
                                                    isDeleted ? 'bg-red-500/5 opacity-60' : 'hover:bg-white/5',
                                                ].join(' ')}
                                            >
                                                <td className="px-4 py-3">
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedRowSet.has(row.rowId)}
                                                        onChange={() => toggleRowSelection(row.rowId)}
                                                        disabled={isSaving}
                                                        className={[
                                                            'h-4 w-4 rounded border-white/20 bg-transparent',
                                                            isSaving ? 'cursor-not-allowed' : 'cursor-pointer',
                                                        ].join(' ')}
                                                    />
                                                </td>
                                                <td className="px-4 py-3 text-gray-400">
                                                    <span>{row.rowId + 1}</span>
                                                </td>
                                                {columns.map((column) => {
                                                    const cellKey = `${row.rowId}:${column}`;
                                                    const isCleared = clearedCellSet.has(cellKey);
                                                    const updatedValue = updatedCellMap.get(cellKey);
                                                    const currentValue = isCleared
                                                        ? ''
                                                        : updatedValue ?? stringifyValue(row.values[column]);

                                                    return (
                                                        <td key={cellKey} className="px-2 py-2">
                                                            <input
                                                                value={currentValue}
                                                                onFocus={() => setActiveCell({ rowId: row.rowId, column })}
                                                                onChange={(event) =>
                                                                    updateCell(row.rowId, column, event.target.value)
                                                                }
                                                                disabled={isDeleted || isSaving}
                                                                className={[
                                                                    'min-w-[160px] rounded-lg border px-3 py-2 text-sm outline-none transition-all',
                                                                    isDeleted || isSaving
                                                                        ? 'cursor-not-allowed border-white/5 bg-white/5 text-gray-500'
                                                                        : 'cursor-pointer border-transparent bg-transparent text-white focus:border-cyan-500/40 focus:bg-cyan-500/5',
                                                                    isCleared || updatedValue !== undefined
                                                                        ? 'border-cyan-500/20 bg-cyan-500/5'
                                                                        : '',
                                                                    activeCell?.rowId === row.rowId && activeCell.column === column
                                                                        ? 'ring-1 ring-cyan-500/30'
                                                                        : '',
                                                                ].join(' ')}
                                                            />
                                                        </td>
                                                    );
                                                })}
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>

                            <div ref={loadMoreRef} className="px-4 py-4 text-center text-sm text-gray-400">
                                {isLoadingMore && 'Daha fazla satir yukleniyor...'}
                                {!isLoadingMore && hasMoreRows && 'Asagi kaydirdikca sonraki satirlar yuklenecek.'}
                                {!hasMoreRows && rows.length > 0 && 'Tum yuklenebilir satirlar gosteriliyor.'}
                            </div>
                        </div>

                        {rows.length === 0 && (
                            <div className="px-4 py-8 text-center text-sm text-gray-400">
                                Goruntulenecek satir bulunamadi.
                            </div>
                        )}
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                        <span className="text-sm text-gray-400">
                            Toplam {totalRows} satir, her chunk icin {pageSize} satir getiriliyor
                        </span>
                        <span className="text-sm text-gray-400">
                            Scroll deneyimi aktif, backend pagination korunuyor
                        </span>
                    </div>
                </div>

                <aside className="space-y-4">
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <div className="mb-4">
                            <h3 className="text-sm font-semibold text-white">Toplu Islemler</h3>
                            <p className="mt-1 text-xs text-gray-400">
                                Text kolonlarini secip bastaki ve sondaki bosluklari tek seferde temizleyin.
                            </p>
                        </div>

                        <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
                            {columns.map((column) => (
                                <label
                                    key={column}
                                    className="flex items-center justify-between gap-3 rounded-xl border border-white/10 px-3 py-2 text-sm text-gray-200"
                                >
                                    <span className="truncate">{column}</span>
                                    <input
                                        type="checkbox"
                                        checked={selectedTrimColumns.includes(column)}
                                        onChange={() => toggleTrimColumnSelection(column)}
                                        disabled={isSaving}
                                        className={[
                                            'h-4 w-4 rounded border-white/20 bg-transparent',
                                            isSaving ? 'cursor-not-allowed' : 'cursor-pointer',
                                        ].join(' ')}
                                    />
                                </label>
                            ))}
                        </div>

                        <button
                            type="button"
                            onClick={applyTrimSelection}
                            disabled={selectedTrimColumns.length === 0 || isSaving}
                            className={[
                                getButtonClassName(selectedTrimColumns.length === 0 || isSaving),
                                'mt-4 w-full justify-center',
                            ].join(' ')}
                        >
                            <Scissors className="h-4 w-4" />
                            Secili Kolonlarda Trim Uygula
                        </button>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <div className="mb-4">
                            <h3 className="text-sm font-semibold text-white">Bekleyen Degisiklikler</h3>
                            <p className="mt-1 text-xs text-gray-400">
                                Kaydetmeden once birikmis duzenlemelerin ozeti.
                            </p>
                        </div>

                        <div className="space-y-3 text-sm text-gray-300">
                            <div className="flex items-center justify-between">
                                <span>Guncellenen hucre</span>
                                <span>{draft.updatedCells.length}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span>Temizlenen hucre</span>
                                <span>{draft.clearedCells.length}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span>Silinecek satir</span>
                                <span>{draft.deletedRowIds.length}</span>
                            </div>
                        </div>

                        <div className="mt-4 space-y-2">
                            <p className="text-xs font-medium uppercase tracking-[0.2em] text-gray-500">
                                Trim Kuyrugu
                            </p>
                            {draft.trimColumns.length === 0 && (
                                <p className="text-sm text-gray-500">Bekleyen trim islemi yok.</p>
                            )}
                            {draft.trimColumns.map((column) => (
                                <div
                                    key={column}
                                    className="flex items-center justify-between gap-3 rounded-xl border border-white/10 px-3 py-2 text-sm text-gray-200"
                                >
                                    <span className="truncate">{column}</span>
                                    <button
                                        type="button"
                                        onClick={() => removeTrimColumn(column)}
                                        disabled={isSaving}
                                        className={getButtonClassName(isSaving)}
                                    >
                                        Kaldir
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </aside>
            </div>
        </div>
    );
}
