'use client';

import {
    type KeyboardEvent as ReactKeyboardEvent,
    type MouseEvent,
    useCallback,
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
import type { DataEditorCellRef, DataEditorCellUpdate } from '@/types/data-upload';

interface DataEditorProps {
    onSaved?: () => Promise<void> | void;
    onDelete?: () => Promise<void> | void;
}

interface EditorClipboard {
    mode: 'copy' | 'cut';
    matrix: string[][];
    sourceCells: DataEditorCellRef[];
    sourceCellKeys: Set<string>;
    preferInternalPaste: boolean;
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

function isTextEntryElement(target: EventTarget | null): boolean {
    if (!(target instanceof HTMLElement)) {
        return false;
    }

    return (
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target.isContentEditable
    );
}

function normalizeClipboardText(text: string): string {
    return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

function parseClipboardText(text: string): string[][] {
    if (!text) {
        return [];
    }

    const normalizedText = normalizeClipboardText(text);
    const rows = normalizedText.split('\n');

    if (rows.length > 1 && rows[rows.length - 1] === '') {
        rows.pop();
    }

    return rows.map((row) => row.split('\t'));
}

function serializeClipboardMatrix(matrix: string[][]): string {
    return matrix.map((row) => row.join('\t')).join('\n');
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

function buildRowRange(start: number, end: number, rowIds: number[]): number[] {
    const startIndex = rowIds.indexOf(start);
    const endIndex = rowIds.indexOf(end);

    if (startIndex < 0 || endIndex < 0) {
        return [end];
    }

    const [minIndex, maxIndex] = startIndex <= endIndex ? [startIndex, endIndex] : [endIndex, startIndex];
    return rowIds.slice(minIndex, maxIndex + 1);
}

export function DataEditor({ onSaved, onDelete }: DataEditorProps) {
    const [isDeleting, setIsDeleting] = useState(false);
    const [selectedCells, setSelectedCells] = useState<DataEditorCellRef[]>([]);
    const [selectionAnchor, setSelectionAnchor] = useState<DataEditorCellRef | null>(null);
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [columnSelectionAnchor, setColumnSelectionAnchor] = useState<string | null>(null);
    const [rowSelectionAnchor, setRowSelectionAnchor] = useState<number | null>(null);
    const [editingCell, setEditingCell] = useState<DataEditorCellRef | null>(null);
    const [editingCellValue, setEditingCellValue] = useState('');
    const [editingColumn, setEditingColumn] = useState<string | null>(null);
    const [editingColumnValue, setEditingColumnValue] = useState('');
    const [editorClipboard, setEditorClipboard] = useState<EditorClipboard | null>(null);
    const editorRootRef = useRef<HTMLDivElement | null>(null);
    const scrollContainerRef = useRef<HTMLDivElement | null>(null);
    const loadMoreRef = useRef<HTMLDivElement | null>(null);
    const skipCellBlurCommitRef = useRef(false);
    const skipColumnBlurCommitRef = useRef(false);
    const isPointerSelectingRef = useRef(false);
    const pointerSelectionStartRef = useRef<DataEditorCellRef | null>(null);
    const isColumnPointerSelectingRef = useRef(false);
    const pointerColumnSelectionStartRef = useRef<string | null>(null);
    const pointerPositionRef = useRef<{ clientX: number; clientY: number } | null>(null);
    const autoScrollFrameRef = useRef<number | null>(null);
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
        replaceSelectedRows,
        toggleAllLoadedRows,
        updateCell,
        updateCells,
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

    const clearTargetCells = useMemo(
        () => (selectedCells.length > 0 ? selectedCells : activeCell ? [activeCell] : []),
        [activeCell, selectedCells]
    );
    const rowIds = useMemo(() => rows.map((row) => row.rowId), [rows]);
    const rowIndexMap = useMemo(
        () => new Map(rowIds.map((rowId, index) => [rowId, index])),
        [rowIds]
    );
    const columnIndexMap = useMemo(
        () => new Map(columns.map((column, index) => [column, index])),
        [columns]
    );
    const updatedCellMap = useMemo(
        () =>
            new Map<string, string>(
                draft.updatedCells.map((cell) => [`${cell.rowId}:${cell.column}`, cell.value])
            ),
        [draft.updatedCells]
    );
    const rowValueMap = useMemo(
        () => new Map(rows.map((row) => [row.rowId, row.values])),
        [rows]
    );
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
    const queuedTrimColumnSet = useMemo(() => new Set(draft.trimColumns), [draft.trimColumns]);
    const availableTrimColumns = useMemo(
        () => columns.filter((column) => !queuedTrimColumnSet.has(column)),
        [columns, queuedTrimColumnSet]
    );
    const copyCellSet = useMemo(
        () => (editorClipboard?.mode === 'copy' ? editorClipboard.sourceCellKeys : new Set<string>()),
        [editorClipboard]
    );
    const cutCellSet = useMemo(
        () => (editorClipboard?.mode === 'cut' ? editorClipboard.sourceCellKeys : new Set<string>()),
        [editorClipboard]
    );
    const allRowsSelected = rows.length > 0 && rows.every((row) => selectedRowSet.has(row.rowId));

    const isEditorShortcutTarget = useCallback(() => {
        const activeElement = document.activeElement;
        if (!activeElement) {
            return true;
        }

        const isInsideEditor =
            activeElement === document.body || editorRootRef.current?.contains(activeElement);

        if (!isInsideEditor) {
            return false;
        }

        return !isTextEntryElement(activeElement);
    }, []);

    const getCurrentCellValue = useCallback((cell: DataEditorCellRef): string => {
        const cellKey = getCellKey(cell);
        if (clearedCellSet.has(cellKey)) {
            return '';
        }

        const updatedValue = updatedCellMap.get(cellKey);
        if (updatedValue !== undefined) {
            return updatedValue;
        }

        return stringifyValue(rowValueMap.get(cell.rowId)?.[cell.column]);
    }, [clearedCellSet, rowValueMap, updatedCellMap]);

    const buildClipboardState = useCallback((
        cells: DataEditorCellRef[],
        mode: 'copy' | 'cut',
        preferInternalPaste: boolean
    ): EditorClipboard | null => {
        if (cells.length === 0) {
            return null;
        }

        const selectedRowIndexes = Array.from(
            new Set(
                cells
                    .map((cell) => rowIndexMap.get(cell.rowId))
                    .filter((index): index is number => index !== undefined)
            )
        ).sort((left, right) => left - right);
        const selectedColumnIndexes = Array.from(
            new Set(
                cells
                    .map((cell) => columnIndexMap.get(cell.column))
                    .filter((index): index is number => index !== undefined)
            )
        ).sort((left, right) => left - right);

        if (selectedRowIndexes.length === 0 || selectedColumnIndexes.length === 0) {
            return null;
        }

        const selectedCellKeys = new Set(cells.map((cell) => getCellKey(cell)));
        const matrix = selectedRowIndexes.map((rowIndex) =>
            selectedColumnIndexes.map((columnIndex) => {
                const cell = {
                    rowId: rowIds[rowIndex],
                    column: columns[columnIndex],
                };

                return selectedCellKeys.has(getCellKey(cell)) ? getCurrentCellValue(cell) : '';
            })
        );

        return {
            mode,
            matrix,
            sourceCells: cells.map((cell) => ({ ...cell })),
            sourceCellKeys: selectedCellKeys,
            preferInternalPaste,
        };
    }, [columnIndexMap, columns, getCurrentCellValue, rowIds, rowIndexMap]);

    const getPasteTargetCell = useCallback((): DataEditorCellRef | null => {
        if (
            activeCell &&
            rowIndexMap.has(activeCell.rowId) &&
            columnIndexMap.has(activeCell.column) &&
            !deletedRowSet.has(activeCell.rowId)
        ) {
            return activeCell;
        }

        if (selectedCells.length === 0) {
            return null;
        }

        return (
            selectedCells
                .filter(
                    (cell) =>
                        rowIndexMap.has(cell.rowId) &&
                        columnIndexMap.has(cell.column) &&
                        !deletedRowSet.has(cell.rowId)
                )
                .sort((left, right) => {
                    const rowDelta =
                        (rowIndexMap.get(left.rowId) ?? Number.MAX_SAFE_INTEGER) -
                        (rowIndexMap.get(right.rowId) ?? Number.MAX_SAFE_INTEGER);

                    if (rowDelta !== 0) {
                        return rowDelta;
                    }

                    return (
                        (columnIndexMap.get(left.column) ?? Number.MAX_SAFE_INTEGER) -
                        (columnIndexMap.get(right.column) ?? Number.MAX_SAFE_INTEGER)
                    );
                })[0] ?? null
        );
    }, [activeCell, columnIndexMap, deletedRowSet, rowIndexMap, selectedCells]);

    const applyClipboardToGrid = useCallback((clipboard: EditorClipboard) => {
        const targetCell = getPasteTargetCell();
        const targetRowIndex = targetCell ? rowIndexMap.get(targetCell.rowId) : undefined;
        const targetColumnIndex = targetCell ? columnIndexMap.get(targetCell.column) : undefined;

        if (
            !targetCell ||
            targetRowIndex === undefined ||
            targetColumnIndex === undefined ||
            clipboard.matrix.length === 0
        ) {
            return;
        }

        const nextUpdatedCells: DataEditorCellUpdate[] = [];
        const destinationCells: DataEditorCellRef[] = [];

        clipboard.matrix.forEach((rowValues, rowOffset) => {
            rowValues.forEach((value, columnOffset) => {
                const nextRowId = rowIds[targetRowIndex + rowOffset];
                const nextColumn = columns[targetColumnIndex + columnOffset];

                if (nextRowId === undefined || nextColumn === undefined || deletedRowSet.has(nextRowId)) {
                    return;
                }

                const cell = { rowId: nextRowId, column: nextColumn };
                nextUpdatedCells.push({ ...cell, value });
                destinationCells.push(cell);
            });
        });

        if (nextUpdatedCells.length === 0) {
            return;
        }

        const destinationCellKeys = new Set(destinationCells.map((cell) => getCellKey(cell)));
        updateCells(nextUpdatedCells);

        if (clipboard.mode === 'cut') {
            const cellsToClear = clipboard.sourceCells.filter(
                (cell) => !destinationCellKeys.has(getCellKey(cell))
            );

            if (cellsToClear.length > 0) {
                clearCells(cellsToClear);
            }

            setEditorClipboard(null);
        } else if (clipboard.preferInternalPaste) {
            setEditorClipboard((previousClipboard) =>
                previousClipboard
                    ? {
                          ...previousClipboard,
                          preferInternalPaste: false,
                      }
                    : previousClipboard
            );
        }

        setSelectionAnchor(destinationCells[0] ?? targetCell);
        setSelectedCells(destinationCells);
        setActiveCell(destinationCells[0] ?? targetCell);
        setSelectedColumns([]);
        setColumnSelectionAnchor(null);
        setRowSelectionAnchor(null);
    }, [
        clearCells,
        columnIndexMap,
        columns,
        deletedRowSet,
        getPasteTargetCell,
        rowIds,
        rowIndexMap,
        setActiveCell,
        updateCells,
    ]);

    const syncClipboard = useCallback(async (mode: 'copy' | 'cut') => {
        if (isSaving || isDeleting || selectedCells.length === 0) {
            return;
        }

        const nextClipboard = buildClipboardState(selectedCells, mode, false);
        if (!nextClipboard) {
            return;
        }

        try {
            await navigator.clipboard.writeText(serializeClipboardMatrix(nextClipboard.matrix));
            setEditorClipboard(nextClipboard);
        } catch {
            setEditorClipboard({
                ...nextClipboard,
                preferInternalPaste: true,
            });
        }
    }, [buildClipboardState, isDeleting, isSaving, selectedCells]);

    const clearCellAndColumnSelection = useCallback(() => {
        setSelectedCells([]);
        setSelectionAnchor(null);
        setSelectedColumns([]);
        setColumnSelectionAnchor(null);
        setActiveCell(null);
        setEditorClipboard(null);
    }, [setActiveCell]);

    const stopAutoScroll = useCallback(() => {
        if (autoScrollFrameRef.current !== null) {
            window.cancelAnimationFrame(autoScrollFrameRef.current);
            autoScrollFrameRef.current = null;
        }
    }, []);

    const syncSelectionWithPointer = useCallback((clientX: number, clientY: number) => {
        const pointerTarget = document.elementFromPoint(clientX, clientY);
        if (!pointerTarget) {
            return;
        }

        if (isPointerSelectingRef.current && pointerSelectionStartRef.current) {
            const cellButton = pointerTarget.closest<HTMLButtonElement>('[data-editor-cell="true"]');
            const rowId = cellButton?.dataset.rowId ? Number(cellButton.dataset.rowId) : NaN;
            const column = cellButton?.dataset.column;

            if (!Number.isNaN(rowId) && column) {
                const cell = { rowId, column };
                setActiveCell(cell);
                setSelectedCells(buildCellRange(pointerSelectionStartRef.current, cell, rowIds, columns));
            }

            return;
        }

        if (isColumnPointerSelectingRef.current && pointerColumnSelectionStartRef.current) {
            const columnButton = pointerTarget.closest<HTMLButtonElement>('[data-editor-column="true"]');
            const column = columnButton?.dataset.column;

            if (column) {
                setSelectedColumns(buildColumnRange(pointerColumnSelectionStartRef.current, column, columns));
            }
        }
    }, [columns, rowIds, setActiveCell]);

    const startAutoScroll = useCallback(() => {
        if (autoScrollFrameRef.current !== null) {
            return;
        }

        const step = () => {
            const scrollContainer = scrollContainerRef.current;
            const pointerPosition = pointerPositionRef.current;

            if (
                !scrollContainer ||
                !pointerPosition ||
                (!isPointerSelectingRef.current && !isColumnPointerSelectingRef.current)
            ) {
                autoScrollFrameRef.current = null;
                return;
            }

            const bounds = scrollContainer.getBoundingClientRect();
            const threshold = 48;
            const maxScrollSpeed = 24;
            let deltaX = 0;
            let deltaY = 0;

            if (pointerPosition.clientX < bounds.left + threshold) {
                deltaX = -Math.min(maxScrollSpeed, bounds.left + threshold - pointerPosition.clientX);
            } else if (pointerPosition.clientX > bounds.right - threshold) {
                deltaX = Math.min(maxScrollSpeed, pointerPosition.clientX - (bounds.right - threshold));
            }

            if (isPointerSelectingRef.current) {
                if (pointerPosition.clientY < bounds.top + threshold) {
                    deltaY = -Math.min(maxScrollSpeed, bounds.top + threshold - pointerPosition.clientY);
                } else if (pointerPosition.clientY > bounds.bottom - threshold) {
                    deltaY = Math.min(maxScrollSpeed, pointerPosition.clientY - (bounds.bottom - threshold));
                }
            }

            if (deltaX !== 0 || deltaY !== 0) {
                scrollContainer.scrollBy({
                    left: deltaX,
                    top: deltaY,
                });
                syncSelectionWithPointer(pointerPosition.clientX, pointerPosition.clientY);
            }

            autoScrollFrameRef.current = window.requestAnimationFrame(step);
        };

        autoScrollFrameRef.current = window.requestAnimationFrame(step);
    }, [syncSelectionWithPointer]);

    const commitCellEditing = useCallback(() => {
        if (!editingCell) {
            return;
        }

        updateCell(editingCell.rowId, editingCell.column, editingCellValue);
        setEditingCell(null);
        setActiveCell(editingCell);
    }, [editingCell, editingCellValue, setActiveCell, updateCell]);

    const cancelCellEditing = useCallback(() => {
        skipCellBlurCommitRef.current = true;
        setEditingCell(null);
    }, []);

    const commitColumnEditing = useCallback(() => {
        if (!editingColumn) {
            return;
        }

        renameColumn(editingColumn, editingColumnValue);
        setEditingColumn(null);
        setSelectedColumns([editingColumn]);
    }, [editingColumn, editingColumnValue, renameColumn]);

    const cancelColumnEditing = useCallback(() => {
        skipColumnBlurCommitRef.current = true;
        setEditingColumn(null);
    }, []);

    const handleCellEditorBlur = useCallback(() => {
        if (skipCellBlurCommitRef.current) {
            skipCellBlurCommitRef.current = false;
            return;
        }

        commitCellEditing();
    }, [commitCellEditing]);

    const handleColumnEditorBlur = useCallback(() => {
        if (skipColumnBlurCommitRef.current) {
            skipColumnBlurCommitRef.current = false;
            return;
        }

        commitColumnEditing();
    }, [commitColumnEditing]);

    useEffect(() => {
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
                return;
            }

            if (event.key === 'Escape' && !editingCell && !editingColumn) {
                event.preventDefault();
                isPointerSelectingRef.current = false;
                pointerSelectionStartRef.current = null;
                isColumnPointerSelectingRef.current = false;
                pointerColumnSelectionStartRef.current = null;
                pointerPositionRef.current = null;
                stopAutoScroll();
                clearCellAndColumnSelection();
                return;
            }

            if ((event.ctrlKey || event.metaKey) && !event.shiftKey && event.key.toLowerCase() === 'c') {
                if (selectedCells.length === 0 || editingCell || editingColumn || isSaving || isDeleting) {
                    return;
                }

                event.preventDefault();
                void syncClipboard('copy');
                return;
            }

            if ((event.ctrlKey || event.metaKey) && !event.shiftKey && event.key.toLowerCase() === 'x') {
                if (selectedCells.length === 0 || editingCell || editingColumn || isSaving || isDeleting) {
                    return;
                }

                event.preventDefault();
                void syncClipboard('cut');
                return;
            }

            if (event.key === 'Delete' && !isSaving && !editingCell && !editingColumn) {
                event.preventDefault();

                if (selectedRows.length > 0) {
                    const deletedSelection = new Set(selectedRows);
                    deleteSelectedRows();
                    setSelectedCells((previousSelectedCells) =>
                        previousSelectedCells.filter((cell) => !deletedSelection.has(cell.rowId))
                    );
                    if (selectionAnchor && deletedSelection.has(selectionAnchor.rowId)) {
                        setSelectionAnchor(null);
                    }
                    if (rowSelectionAnchor && deletedSelection.has(rowSelectionAnchor)) {
                        setRowSelectionAnchor(null);
                    }
                    return;
                }

                if (clearTargetCells.length > 0) {
                    clearCells(clearTargetCells);
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [
        clearCells,
        clearTargetCells,
        deleteSelectedRows,
        editorClipboard,
        editingCell,
        editingColumn,
        clearCellAndColumnSelection,
        isDeleting,
        isDirty,
        isSaving,
        rowSelectionAnchor,
        saveChanges,
        selectedCells,
        selectedRows,
        selectionAnchor,
        isEditorShortcutTarget,
        stopAutoScroll,
        syncClipboard,
        undoLastChange,
    ]);

    useEffect(() => {
        const handlePointerMove = (event: globalThis.MouseEvent) => {
            if (!isPointerSelectingRef.current && !isColumnPointerSelectingRef.current) {
                return;
            }

            pointerPositionRef.current = {
                clientX: event.clientX,
                clientY: event.clientY,
            };
            syncSelectionWithPointer(event.clientX, event.clientY);
            startAutoScroll();
        };

        const handlePointerSelectionEnd = () => {
            isPointerSelectingRef.current = false;
            pointerSelectionStartRef.current = null;
            isColumnPointerSelectingRef.current = false;
            pointerColumnSelectionStartRef.current = null;
            pointerPositionRef.current = null;
            stopAutoScroll();
        };

        window.addEventListener('mousemove', handlePointerMove);
        window.addEventListener('mouseup', handlePointerSelectionEnd);

        return () => {
            window.removeEventListener('mousemove', handlePointerMove);
            window.removeEventListener('mouseup', handlePointerSelectionEnd);
            stopAutoScroll();
        };
    }, [startAutoScroll, stopAutoScroll, syncSelectionWithPointer]);

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

    useEffect(() => {
        const handlePaste = (event: ClipboardEvent) => {
            if (!isEditorShortcutTarget() || isSaving || isDeleting || editingCell || editingColumn) {
                return;
            }

            const clipboardText = event.clipboardData?.getData('text/plain') ?? '';
            const externalMatrix = parseClipboardText(clipboardText);
            const serializedInternalClipboard = editorClipboard
                ? normalizeClipboardText(serializeClipboardMatrix(editorClipboard.matrix))
                : null;
            const shouldUseInternalClipboard =
                !!editorClipboard &&
                (editorClipboard.mode === 'cut' ||
                    editorClipboard.preferInternalPaste ||
                    normalizeClipboardText(clipboardText) === serializedInternalClipboard);
            const nextClipboard =
                shouldUseInternalClipboard
                    ? editorClipboard
                    : externalMatrix.length > 0
                      ? {
                            mode: 'copy' as const,
                            matrix: externalMatrix,
                            sourceCells: [],
                            sourceCellKeys: new Set<string>(),
                            preferInternalPaste: false,
                        }
                      : editorClipboard;

            if (!nextClipboard || nextClipboard.matrix.length === 0) {
                return;
            }

            event.preventDefault();
            applyClipboardToGrid(nextClipboard);
        };

        window.addEventListener('paste', handlePaste);
        return () => window.removeEventListener('paste', handlePaste);
    }, [
        applyClipboardToGrid,
        editingCell,
        editingColumn,
        editorClipboard,
        isEditorShortcutTarget,
        isDeleting,
        isSaving,
    ]);

    useEffect(() => {
        const validRowIds = new Set(rows.map((row) => row.rowId));
        const validColumns = new Set(columns);

        setEditorClipboard((previousClipboard) => {
            if (!previousClipboard) {
                return previousClipboard;
            }

            const isClipboardStillValid = previousClipboard.sourceCells.every(
                (cell) =>
                    validRowIds.has(cell.rowId) &&
                    validColumns.has(cell.column) &&
                    !deletedRowSet.has(cell.rowId)
            );

            return isClipboardStillValid ? previousClipboard : null;
        });
    }, [columns, deletedRowSet, rows]);

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
        setRowSelectionAnchor((previousRowAnchor) =>
            previousRowAnchor !== null && validRowIds.has(previousRowAnchor) ? previousRowAnchor : null
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
        pointerPositionRef.current = {
            clientX: event.clientX,
            clientY: event.clientY,
        };
        startAutoScroll();
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
        setRowSelectionAnchor(null);

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
        pointerPositionRef.current = {
            clientX: event.clientX,
            clientY: event.clientY,
        };
        startAutoScroll();
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
        setEditingCellValue(getCurrentCellValue(cell));
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
        setRowSelectionAnchor(null);
        setColumnSelectionAnchor(column);
        setSelectedColumns([column]);
        setEditingColumnValue(getColumnDisplayName(column));
        setEditingColumn(column);
    };

    const handleRowCheckboxClick = (rowId: number, event: MouseEvent<HTMLInputElement>) => {
        if (isSaving) {
            return;
        }

        event.stopPropagation();

        if (event.shiftKey && rowSelectionAnchor !== null) {
            replaceSelectedRows(buildRowRange(rowSelectionAnchor, rowId, rowIds));
            return;
        }

        setRowSelectionAnchor(rowId);
        toggleRowSelection(rowId);
    };

    const handleCellEditorKeyDown = (
        event: ReactKeyboardEvent<HTMLInputElement>
    ) => {
        if (event.key === 'Enter' || event.key === 'Tab') {
            event.preventDefault();
            commitCellEditing();
            return;
        }

        if (event.key === 'Escape') {
            event.preventDefault();
            cancelCellEditing();
        }
    };

    const handleColumnEditorKeyDown = (
        event: ReactKeyboardEvent<HTMLInputElement>
    ) => {
        if (event.key === 'Enter' || event.key === 'Tab') {
            event.preventDefault();
            commitColumnEditing();
            return;
        }

        if (event.key === 'Escape') {
            event.preventDefault();
            cancelColumnEditing();
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
                        <span className="rounded-full border border-white/10 px-3 py-1">
                            Kısayollar: Ctrl+C / Ctrl+X / Ctrl+V
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
                            clearCellAndColumnSelection();
                            setRowSelectionAnchor(null);
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
                                    clearCellAndColumnSelection();
                                    setRowSelectionAnchor(null);
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
                                Seçili hücre: {selectedCells.length}
                            </span>
                            <span className="rounded-full border border-white/10 px-3 py-1">
                                Seçili sütun: {selectedColumns.length}
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
                                    if (rowSelectionAnchor && deletedSelection.has(rowSelectionAnchor)) {
                                        setRowSelectionAnchor(null);
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
                                                disabled={isSaving}
                                                className={[
                                                    'h-4 w-4 rounded border-white/20 bg-transparent',
                                                    isSaving ? 'cursor-not-allowed' : 'cursor-pointer',
                                                ].join(' ')}
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
                                                        value={editingColumnValue}
                                                        onChange={(event) =>
                                                            setEditingColumnValue(event.target.value)
                                                        }
                                                        onBlur={handleColumnEditorBlur}
                                                        onKeyDown={handleColumnEditorKeyDown}
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
                                                        data-editor-column="true"
                                                        data-column={column}
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
                                                        readOnly
                                                        onClick={(event) => handleRowCheckboxClick(row.rowId, event)}
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
                                                    const isCopyCell = copyCellSet.has(cellKey);
                                                    const isCutCell = cutCellSet.has(cellKey);
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
                                                                    value={editingCellValue}
                                                                    onFocus={() =>
                                                                        setActiveCell({ rowId: row.rowId, column })
                                                                    }
                                                                    onBlur={handleCellEditorBlur}
                                                                    onKeyDown={handleCellEditorKeyDown}
                                                                    onChange={(event) =>
                                                                        setEditingCellValue(event.target.value)
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
                                                                    data-editor-cell="true"
                                                                    data-row-id={row.rowId}
                                                                    data-column={column}
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
                                                                        'relative block min-w-[160px] w-full overflow-hidden rounded-lg border px-3 py-2 text-left text-sm outline-none transition-all',
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
                                                                        isCutCell
                                                                            ? 'border-amber-400/60 border-dashed bg-amber-500/10'
                                                                            : '',
                                                                        isSelectedCell
                                                                            ? 'border-cyan-400 bg-cyan-500/10 shadow-[0_0_0_1px_rgba(34,211,238,0.18)]'
                                                                            : '',
                                                                    ].join(' ')}
                                                                >
                                                                    <span className="block min-h-[1.5rem] truncate">
                                                                        {currentValue || '\u00A0'}
                                                                    </span>
                                                                    {isCopyCell && (
                                                                        <span
                                                                            aria-hidden="true"
                                                                            className="data-editor-copy-ants"
                                                                        />
                                                                    )}
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
                            Toplam {totalRows} satır, her parça için {pageSize} satır getiriliyor
                        </span>
                        <span className="text-sm text-gray-400">
                            Kaydırma deneyimi aktif, arka uç sayfalama korunuyor
                        </span>
                    </div>
                </div>

                <aside className="space-y-4">
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <div className="mb-4">
                            <h3 className="text-sm font-semibold text-white">Toplu İşlemler</h3>
                            <p className="mt-1 text-xs text-gray-400">
                                Metin sütunlarını seçip baştaki ve sondaki boşlukları tek seferde temizleyin.
                            </p>
                        </div>

                        <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
                            {availableTrimColumns.length === 0 && (
                                <p className="rounded-xl border border-white/10 px-3 py-4 text-sm text-gray-500">
                                    Kuyrukta olmayan kırpma sütunu kalmadı.
                                </p>
                            )}
                            {availableTrimColumns.map((column) => (
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
                            Seçili sütunlarda kırpma uygula
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
                                <span>Yeniden adlandırılan sütun</span>
                                <span>{draft.renamedColumns.length}</span>
                            </div>
                        </div>

                        <div className="mt-4 space-y-2">
                            <p className="text-xs font-medium uppercase tracking-[0.2em] text-gray-500">
                                Kırpma Kuyruğu
                            </p>
                            {draft.trimColumns.length === 0 && (
                                <p className="text-sm text-gray-500">Bekleyen kırpma işlemi yok.</p>
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
