'use client';

import {
    type KeyboardEvent as ReactKeyboardEvent,
    type MouseEvent,
    useEffect,
    useMemo,
    useRef,
    useState,
} from 'react';
import {
    Eraser,
    RotateCcw,
    Save,
    Scissors,
    Trash2,
    XCircle,
} from 'lucide-react';
import { useDataEditor } from '@/hooks/useDataEditor';
import type { DataEditorCellRef } from '@/types/data-upload';

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

function getCellKey(cell: DataEditorCellRef): string {
    return `${cell.rowId}:${cell.column}`;
}

function buildCellRange(
    start: DataEditorCellRef,
    end: DataEditorCellRef,
    rowIds: number[],
    columns: string[]
): DataEditorCellRef[] {
    const startRowIndex = rowIds.indexOf(start.rowId);
    const endRowIndex = rowIds.indexOf(end.rowId);
    const startColumnIndex = columns.indexOf(start.column);
    const endColumnIndex = columns.indexOf(end.column);

    if (startRowIndex < 0 || endRowIndex < 0 || startColumnIndex < 0 || endColumnIndex < 0) {
        return [end];
    }

    const [minRowIndex, maxRowIndex] =
        startRowIndex <= endRowIndex ? [startRowIndex, endRowIndex] : [endRowIndex, startRowIndex];
    const [minColumnIndex, maxColumnIndex] =
        startColumnIndex <= endColumnIndex
            ? [startColumnIndex, endColumnIndex]
            : [endColumnIndex, startColumnIndex];

    const selectedCells: DataEditorCellRef[] = [];
    for (let rowIndex = minRowIndex; rowIndex <= maxRowIndex; rowIndex += 1) {
        for (let columnIndex = minColumnIndex; columnIndex <= maxColumnIndex; columnIndex += 1) {
            selectedCells.push({
                rowId: rowIds[rowIndex],
                column: columns[columnIndex],
            });
        }
    }

    return selectedCells;
}

function buildColumnRange(start: string, end: string, columns: string[]): string[] {
    const startIndex = columns.indexOf(start);
    const endIndex = columns.indexOf(end);

    if (startIndex < 0 || endIndex < 0) {
        return [end];
    }

    const [minIndex, maxIndex] = startIndex <= endIndex ? [startIndex, endIndex] : [endIndex, startIndex];
    return columns.slice(minIndex, maxIndex + 1);
}

export function DataEditor({ onSaved, onDelete }: DataEditorProps) {
    const [isDeleting, setIsDeleting] = useState(false);
    const [selectedCells, setSelectedCells] = useState<DataEditorCellRef[]>([]);
    const [selectionAnchor, setSelectionAnchor] = useState<DataEditorCellRef | null>(null);
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [columnSelectionAnchor, setColumnSelectionAnchor] = useState<string | null>(null);
    const [editingCell, setEditingCell] = useState<DataEditorCellRef | null>(null);
    const [editingColumn, setEditingColumn] = useState<string | null>(null);
    const editorRootRef = useRef<HTMLDivElement | null>(null);
    const scrollContainerRef = useRef<HTMLDivElement | null>(null);
    const loadMoreRef = useRef<HTMLDivElement | null>(null);
    const isPointerSelectingRef = useRef(false);
    const pointerSelectionStartRef = useRef<DataEditorCellRef | null>(null);
    const isColumnPointerSelectingRef = useRef(false);
    const pointerColumnSelectionStartRef = useRef<string | null>(null);
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
        renameColumn,
        getColumnDisplayName,
        clearCells,
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
            'Yüklenen veri seti silinecek ve bu oturumdaki düzenlemeler kaybolacak. Devam etmek istiyor musunuz?'
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
        const isEditorShortcutTarget = () => {
            const activeElement = document.activeElement;
            if (!activeElement) {
                return true;
            }

            return activeElement === document.body || editorRootRef.current?.contains(activeElement);
        };

        const handleKeyDown = (event: KeyboardEvent) => {
            if (!isEditorShortcutTarget()) {
                return;
            }

            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
                if (!isDirty || isSaving) {
                    return;
                }

                event.preventDefault();
                void saveChanges();
                return;
            }

            if (
                (event.ctrlKey || event.metaKey) &&
                !event.shiftKey &&
                event.key.toLowerCase() === 'z'
            ) {
                if (!isDirty || isSaving) {
                    return;
                }

                event.preventDefault();
                undoLastChange();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isDirty, isSaving, saveChanges, undoLastChange]);

    useEffect(() => {
        const handlePointerSelectionEnd = () => {
            isPointerSelectingRef.current = false;
            pointerSelectionStartRef.current = null;
            isColumnPointerSelectingRef.current = false;
            pointerColumnSelectionStartRef.current = null;
        };

        window.addEventListener('mouseup', handlePointerSelectionEnd);
        return () => window.removeEventListener('mouseup', handlePointerSelectionEnd);
    }, []);

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
    const rowIds = useMemo(() => rows.map((row) => row.rowId), [rows]);
    const clearedCellSet = useMemo(
        () => new Set<string>(draft.clearedCells.map((cell) => `${cell.rowId}:${cell.column}`)),
        [draft.clearedCells]
    );
    const deletedRowSet = useMemo(() => new Set(draft.deletedRowIds), [draft.deletedRowIds]);
    const selectedRowSet = useMemo(() => new Set(selectedRows), [selectedRows]);
    const selectedCellSet = useMemo(
        () => new Set(selectedCells.map((cell) => getCellKey(cell))),
        [selectedCells]
    );
    const selectedColumnSet = useMemo(() => new Set(selectedColumns), [selectedColumns]);
    const allRowsSelected = rows.length > 0 && rows.every((row) => selectedRowSet.has(row.rowId));
    const clearTargetCells = selectedCells.length > 0 ? selectedCells : activeCell ? [activeCell] : [];

    useEffect(() => {
        const validRowIds = new Set(rows.map((row) => row.rowId));
        const validColumns = new Set(columns);

        setSelectedCells((previousSelectedCells) =>
            previousSelectedCells.filter(
                (cell) =>
                    validRowIds.has(cell.rowId) &&
                    validColumns.has(cell.column) &&
                    !deletedRowSet.has(cell.rowId)
            )
        );
        setSelectionAnchor((previousAnchor) => {
            if (
                previousAnchor &&
                validRowIds.has(previousAnchor.rowId) &&
                validColumns.has(previousAnchor.column) &&
                !deletedRowSet.has(previousAnchor.rowId)
            ) {
                return previousAnchor;
            }

            return null;
        });
        setEditingCell((previousEditingCell) => {
            if (
                previousEditingCell &&
                validRowIds.has(previousEditingCell.rowId) &&
                validColumns.has(previousEditingCell.column) &&
                !deletedRowSet.has(previousEditingCell.rowId)
            ) {
                return previousEditingCell;
            }

            return null;
        });
        setSelectedColumns((previousSelectedColumns) =>
            previousSelectedColumns.filter((column) => validColumns.has(column))
        );
        setColumnSelectionAnchor((previousColumnAnchor) =>
            previousColumnAnchor && validColumns.has(previousColumnAnchor) ? previousColumnAnchor : null
        );
        setEditingColumn((previousEditingColumn) =>
            previousEditingColumn && validColumns.has(previousEditingColumn) ? previousEditingColumn : null
        );
    }, [columns, deletedRowSet, rows]);

    const handleCellMouseDown = (cell: DataEditorCellRef, event: MouseEvent<HTMLButtonElement>) => {
        if (isSaving) {
            return;
        }

        setEditingColumn(null);
        setSelectedColumns([]);
        setColumnSelectionAnchor(null);

        if (event.shiftKey && selectionAnchor) {
            event.preventDefault();
            setSelectedCells(buildCellRange(selectionAnchor, cell, rowIds, columns));
            setActiveCell(cell);
            return;
        }

        if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            setSelectionAnchor(cell);
            setActiveCell(cell);
            setSelectedCells((previousSelectedCells) => {
                const cellKey = getCellKey(cell);
                const alreadySelected = previousSelectedCells.some(
                    (selectedCell) => getCellKey(selectedCell) === cellKey
                );

                if (alreadySelected) {
                    return previousSelectedCells.filter(
                        (selectedCell) => getCellKey(selectedCell) !== cellKey
                    );
                }

                return [...previousSelectedCells, cell];
            });
            return;
        }

        isPointerSelectingRef.current = true;
        pointerSelectionStartRef.current = cell;
        setSelectionAnchor(cell);
        setActiveCell(cell);
        setSelectedCells([cell]);
    };

    const handleCellMouseEnter = (cell: DataEditorCellRef) => {
        if (!isPointerSelectingRef.current || !pointerSelectionStartRef.current) {
            return;
        }

        setActiveCell(cell);
        setSelectedCells(buildCellRange(pointerSelectionStartRef.current, cell, rowIds, columns));
    };

    const handleColumnMouseDown = (column: string, event: MouseEvent<HTMLButtonElement>) => {
        if (isSaving) {
            return;
        }

        event.preventDefault();
        setEditingCell(null);
        setActiveCell(null);
        setSelectedCells([]);
        setSelectionAnchor(null);

        if (event.shiftKey && columnSelectionAnchor) {
            setSelectedColumns(buildColumnRange(columnSelectionAnchor, column, columns));
            return;
        }

        if (event.ctrlKey || event.metaKey) {
            setColumnSelectionAnchor(column);
            setSelectedColumns((previousSelectedColumns) =>
                previousSelectedColumns.includes(column)
                    ? previousSelectedColumns.filter((selectedColumn) => selectedColumn !== column)
                    : [...previousSelectedColumns, column]
            );
            return;
        }

        isColumnPointerSelectingRef.current = true;
        pointerColumnSelectionStartRef.current = column;
        setColumnSelectionAnchor(column);
        setSelectedColumns([column]);
    };

    const handleColumnMouseEnter = (column: string) => {
        if (!isColumnPointerSelectingRef.current || !pointerColumnSelectionStartRef.current) {
            return;
        }

        setSelectedColumns(
            buildColumnRange(pointerColumnSelectionStartRef.current, column, columns)
        );
    };

    const handleCellDoubleClick = (cell: DataEditorCellRef) => {
        if (isSaving || deletedRowSet.has(cell.rowId)) {
            return;
        }

        setSelectedColumns([]);
        setColumnSelectionAnchor(null);
        setEditingColumn(null);
        setSelectionAnchor(cell);
        setActiveCell(cell);
        setSelectedCells([cell]);
        setEditingCell(cell);
    };

    const handleColumnDoubleClick = (column: string) => {
        if (isSaving) {
            return;
        }

        setEditingCell(null);
        setActiveCell(null);
        setSelectedCells([]);
        setSelectionAnchor(null);
        setColumnSelectionAnchor(column);
        setSelectedColumns([column]);
        setEditingColumn(column);
    };

    const handleCellEditorKeyDown = (
        event: ReactKeyboardEvent<HTMLInputElement>,
        cell: DataEditorCellRef
    ) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            setEditingCell(null);
            setActiveCell(cell);
            return;
        }

        if (event.key === 'Escape') {
            event.preventDefault();
            setEditingCell(null);
        }
    };

    const handleColumnEditorKeyDown = (
        event: ReactKeyboardEvent<HTMLInputElement>,
        column: string
    ) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            setEditingColumn(null);
            setSelectedColumns([column]);
            return;
        }

        if (event.key === 'Escape') {
            event.preventDefault();
            setEditingColumn(null);
        }
    };

    if (isLoading && rows.length === 0) {
        return (
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-6 text-sm text-gray-400">
                Veri düzenleyici yükleniyor...
            </div>
        );
    }

    return (
        <div ref={editorRootRef} className="space-y-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-2">
                    <div>
                        <h2 className="text-xl font-semibold text-white">Veri Düzenleme</h2>
                        <p className="text-sm text-gray-400">
                            Veriler parçalı olarak yüklenir. Kaydırdıkça yeni satırlar gelir, değişiklikler yalnızca kaydettiğinizde uygulanır.
                        </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400">
                        <span className="rounded-full border border-white/10 px-3 py-1">
                            Toplam satır: {totalRows}
                        </span>
                        <span className="rounded-full border border-white/10 px-3 py-1">
                            Yüklenen satır: {rows.length}
                        </span>
                        <span className="rounded-full border border-white/10 px-3 py-1">
                            Kaydedilmemiş değişiklik: {isDirty ? 'Var' : 'Yok'}
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
                        onClick={() => {
                            discardChanges();
                            setSelectedCells([]);
                            setSelectionAnchor(null);
                            setSelectedColumns([]);
                            setColumnSelectionAnchor(null);
                            setEditingCell(null);
                            setEditingColumn(null);
                        }}
                        disabled={!isDirty || isSaving}
                        className={getButtonClassName(!isDirty || isSaving)}
                    >
                        <XCircle className="h-4 w-4" />
                        Vazgeç
                    </button>
                    <button
                        type="button"
                        onClick={() => {
                            void (async () => {
                                const didSave = await saveChanges();
                                if (didSave) {
                                    setSelectedCells([]);
                                    setSelectionAnchor(null);
                                    setSelectedColumns([]);
                                    setColumnSelectionAnchor(null);
                                    setEditingCell(null);
                                    setEditingColumn(null);
                                }
                            })();
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
                                Yüklenen bölüm: {loadedPages} / {totalPages}
                            </span>
                            <span className="rounded-full border border-white/10 px-3 py-1">
                                Seçili satır: {selectedRows.length}
                            </span>
                            <span className="rounded-full border border-white/10 px-3 py-1">
                                Silinecek satır: {draft.deletedRowIds.length}
                            </span>
                            <span className="rounded-full border border-white/10 px-3 py-1">
                                Secili hucre: {selectedCells.length}
                            </span>
                            <span className="rounded-full border border-white/10 px-3 py-1">
                                Secili sutun: {selectedColumns.length}
                            </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                            <button
                                type="button"
                                onClick={() => clearCells(clearTargetCells)}
                                disabled={clearTargetCells.length === 0 || isSaving}
                                className={getButtonClassName(clearTargetCells.length === 0 || isSaving)}
                            >
                                <Eraser className="h-4 w-4" />
                                Seçili Hücreyi Temizle
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    const deletedSelection = new Set(selectedRows);
                                    deleteSelectedRows();
                                    setSelectedCells((previousSelectedCells) =>
                                        previousSelectedCells.filter(
                                            (cell) => !deletedSelection.has(cell.rowId)
                                        )
                                    );
                                    if (selectionAnchor && deletedSelection.has(selectionAnchor.rowId)) {
                                        setSelectionAnchor(null);
                                    }
                                }}
                                disabled={selectedRows.length === 0 || isSaving}
                                className={getButtonClassName(selectedRows.length === 0 || isSaving, 'danger')}
                            >
                                <Trash2 className="h-4 w-4" />
                                Seçili Satırları Sil
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
                                                {editingColumn === column ? (
                                                    <input
                                                        autoFocus
                                                        value={getColumnDisplayName(column)}
                                                        onChange={(event) =>
                                                            renameColumn(column, event.target.value)
                                                        }
                                                        onBlur={() => setEditingColumn(null)}
                                                        onKeyDown={(event) =>
                                                            handleColumnEditorKeyDown(event, column)
                                                        }
                                                        disabled={isSaving}
                                                        className={[
                                                            'block min-w-[160px] w-full rounded-lg border px-3 py-2 text-sm outline-none transition-all',
                                                            isSaving
                                                                ? 'cursor-not-allowed border-white/5 bg-white/5 text-gray-500'
                                                                : 'border-cyan-400 bg-cyan-500/10 text-white focus:border-cyan-400 focus:bg-cyan-500/10',
                                                        ].join(' ')}
                                                    />
                                                ) : (
                                                    <button
                                                        type="button"
                                                        onMouseDown={(event) =>
                                                            handleColumnMouseDown(column, event)
                                                        }
                                                        onMouseEnter={() => handleColumnMouseEnter(column)}
                                                        onDoubleClick={() => handleColumnDoubleClick(column)}
                                                        disabled={isSaving}
                                                        className={[
                                                            'block min-w-[160px] w-full rounded-lg border px-3 py-2 text-left text-sm outline-none transition-all',
                                                            isSaving
                                                                ? 'cursor-not-allowed border-white/5 bg-white/5 text-gray-500'
                                                                : 'cursor-pointer border-transparent bg-transparent text-gray-200',
                                                            draft.renamedColumns.some(
                                                                (item) => item.column === column
                                                            )
                                                                ? 'bg-cyan-500/5'
                                                                : '',
                                                            selectedColumnSet.has(column)
                                                                ? 'border-cyan-400 bg-cyan-500/10 text-white shadow-[0_0_0_1px_rgba(34,211,238,0.18)]'
                                                                : '',
                                                        ].join(' ')}
                                                    >
                                                        <span className="block truncate">
                                                            {getColumnDisplayName(column)}
                                                        </span>
                                                    </button>
                                                )}
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
                                                    const isSelectedCell = selectedCellSet.has(cellKey);
                                                    const isEditingCell =
                                                        editingCell?.rowId === row.rowId &&
                                                        editingCell.column === column;
                                                    const isCleared = clearedCellSet.has(cellKey);
                                                    const updatedValue = updatedCellMap.get(cellKey);
                                                    const currentValue = isCleared
                                                        ? ''
                                                        : updatedValue ?? stringifyValue(row.values[column]);

                                                    return (
                                                        <td key={cellKey} className="relative px-2 py-2">
                                                            {isEditingCell ? (
                                                                <input
                                                                    autoFocus
                                                                    value={currentValue}
                                                                    onFocus={() =>
                                                                        setActiveCell({ rowId: row.rowId, column })
                                                                    }
                                                                    onBlur={() => setEditingCell(null)}
                                                                    onKeyDown={(event) =>
                                                                        handleCellEditorKeyDown(event, {
                                                                            rowId: row.rowId,
                                                                            column,
                                                                        })
                                                                    }
                                                                    onChange={(event) =>
                                                                        updateCell(row.rowId, column, event.target.value)
                                                                    }
                                                                    disabled={isDeleted || isSaving}
                                                                    className={[
                                                                        'block min-w-[160px] w-full rounded-lg border px-3 py-2 text-sm outline-none transition-all',
                                                                        isDeleted || isSaving
                                                                            ? 'cursor-not-allowed border-white/5 bg-white/5 text-gray-500'
                                                                            : 'border-cyan-400 bg-cyan-500/10 text-white focus:border-cyan-400 focus:bg-cyan-500/10',
                                                                    ].join(' ')}
                                                                />
                                                            ) : (
                                                                <button
                                                                    type="button"
                                                                    onMouseDown={(event) =>
                                                                        handleCellMouseDown(
                                                                            { rowId: row.rowId, column },
                                                                            event
                                                                        )
                                                                    }
                                                                    onMouseEnter={() =>
                                                                        handleCellMouseEnter({
                                                                            rowId: row.rowId,
                                                                            column,
                                                                        })
                                                                    }
                                                                    onDoubleClick={() =>
                                                                        handleCellDoubleClick({
                                                                            rowId: row.rowId,
                                                                            column,
                                                                        })
                                                                    }
                                                                    disabled={isDeleted || isSaving}
                                                                    className={[
                                                                        'block min-w-[160px] w-full rounded-lg border px-3 py-2 text-left text-sm outline-none transition-all',
                                                                        isDeleted || isSaving
                                                                            ? 'cursor-not-allowed border-white/5 bg-white/5 text-gray-500'
                                                                            : 'cursor-pointer border-transparent bg-transparent text-white',
                                                                        isCleared || updatedValue !== undefined
                                                                            ? 'border-cyan-500/20 bg-cyan-500/5'
                                                                            : '',
                                                                        activeCell?.rowId === row.rowId &&
                                                                        activeCell.column === column &&
                                                                        !isSelectedCell
                                                                            ? 'ring-1 ring-cyan-500/30'
                                                                            : '',
                                                                        isSelectedCell
                                                                            ? 'border-cyan-400 bg-cyan-500/10 shadow-[0_0_0_1px_rgba(34,211,238,0.18)]'
                                                                            : '',
                                                                    ].join(' ')}
                                                                >
                                                                    <span className="block min-h-[1.5rem] truncate">
                                                                        {currentValue || '\u00A0'}
                                                                    </span>
                                                                </button>
                                                            )}
                                                        </td>
                                                    );
                                                })}
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>

                            <div ref={loadMoreRef} className="px-4 py-4 text-center text-sm text-gray-400">
                                {isLoadingMore && 'Daha fazla satır yükleniyor...'}
                                {!isLoadingMore && hasMoreRows && 'Aşağı kaydırdıkça sonraki satırlar yüklenecek.'}
                                {!hasMoreRows && rows.length > 0 && 'Tüm yüklenebilir satırlar gösteriliyor.'}
                            </div>
                        </div>

                        {rows.length === 0 && (
                            <div className="px-4 py-8 text-center text-sm text-gray-400">
                                Görüntülenecek satır bulunamadı.
                            </div>
                        )}
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                        <span className="text-sm text-gray-400">
                            Toplam {totalRows} satır, her chunk için {pageSize} satır getiriliyor
                        </span>
                        <span className="text-sm text-gray-400">
                            Scroll deneyimi aktif, backend pagination korunuyor
                        </span>
                    </div>
                </div>

                <aside className="space-y-4">
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <div className="mb-4">
                            <h3 className="text-sm font-semibold text-white">Toplu İşlemler</h3>
                            <p className="mt-1 text-xs text-gray-400">
                                Text kolonlarını seçip baştaki ve sondaki boşlukları tek seferde temizleyin.
                            </p>
                        </div>

                        <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
                            {columns.map((column) => (
                                <label
                                    key={column}
                                    className="flex items-center justify-between gap-3 rounded-xl border border-white/10 px-3 py-2 text-sm text-gray-200"
                                >
                                    <span className="truncate">{getColumnDisplayName(column)}</span>
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
                            Seçili Kolonlarda Trim Uygula
                        </button>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <div className="mb-4">
                            <h3 className="text-sm font-semibold text-white">Bekleyen Değişiklikler</h3>
                            <p className="mt-1 text-xs text-gray-400">
                                Kaydetmeden önce birikmiş düzenlemelerin özeti.
                            </p>
                        </div>

                        <div className="space-y-3 text-sm text-gray-300">
                            <div className="flex items-center justify-between">
                                <span>Güncellenen hücre</span>
                                <span>{draft.updatedCells.length}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span>Temizlenen hücre</span>
                                <span>{draft.clearedCells.length}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span>Silinecek satır</span>
                                <span>{draft.deletedRowIds.length}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span>Rename sutun</span>
                                <span>{draft.renamedColumns.length}</span>
                            </div>
                        </div>

                        <div className="mt-4 space-y-2">
                            <p className="text-xs font-medium uppercase tracking-[0.2em] text-gray-500">
                                Trim Kuyruğu
                            </p>
                            {draft.trimColumns.length === 0 && (
                                <p className="text-sm text-gray-500">Bekleyen trim işlemi yok.</p>
                            )}
                            {draft.trimColumns.map((column) => (
                                <div
                                    key={column}
                                    className="flex items-center justify-between gap-3 rounded-xl border border-white/10 px-3 py-2 text-sm text-gray-200"
                                >
                                    <span className="truncate">{getColumnDisplayName(column)}</span>
                                    <button
                                        type="button"
                                        onClick={() => removeTrimColumn(column)}
                                        disabled={isSaving}
                                        className={getButtonClassName(isSaving)}
                                    >
                                        Kaldır
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
