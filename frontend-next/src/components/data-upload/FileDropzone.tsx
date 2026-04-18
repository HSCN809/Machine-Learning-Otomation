'use client';

import { useCallback, useState } from 'react';
import { Upload, File, X, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';

interface FileDropzoneProps {
    onFileSelect: (file: File) => void;
    accept?: string;
    maxSize?: number; // in bytes
    disabled?: boolean;
}

export function FileDropzone({
    onFileSelect,
    accept = '.csv,.xlsx,.xls',
    maxSize = 200 * 1024 * 1024, // 200MB
    disabled = false,
}: FileDropzoneProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const validateFile = useCallback((file: File): string | null => {
        // Check file type
        const validExtensions = accept.split(',').map(ext => ext.trim().toLowerCase());
        const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();

        if (!validExtensions.includes(fileExt)) {
            return `Desteklenmeyen format: ${fileExt}. Desteklenen: ${validExtensions.join(', ')}`;
        }

        // Check file size
        if (file.size > maxSize) {
            return `Dosya boyutu çok büyük: ${(file.size / 1024 / 1024).toFixed(2)}MB. Maksimum: ${(maxSize / 1024 / 1024).toFixed(0)}MB`;
        }

        return null;
    }, [accept, maxSize]);

    const handleFile = useCallback((file: File) => {
        setError(null);
        const validationError = validateFile(file);

        if (validationError) {
            setError(validationError);
            return;
        }

        onFileSelect(file);
    }, [validateFile, onFileSelect]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!disabled) setIsDragging(true);
    }, [disabled]);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        if (disabled) return;

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    }, [disabled, handleFile]);

    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            handleFile(files[0]);
        }
    }, [handleFile]);

    return (
        <div className="space-y-3">
            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                    'relative rounded-2xl border-2 border-dashed p-8 transition-all duration-300 cursor-pointer',
                    'flex flex-col items-center justify-center text-center min-h-[200px]',
                    isDragging && 'border-cyan-500 bg-cyan-500/10',
                    !isDragging && 'border-white/20 hover:border-cyan-500/50 hover:bg-white/5',
                    disabled && 'opacity-50 cursor-not-allowed',
                    error && 'border-red-500/50'
                )}
            >
                {/* Glow effect when dragging */}
                {isDragging && (
                    <div
                        className="absolute inset-0 rounded-2xl opacity-20 pointer-events-none"
                        style={{
                            background: `radial-gradient(circle at center, ${theme.colors.primary.cyan} 0%, transparent 70%)`,
                        }}
                    />
                )}

                <input
                    type="file"
                    accept={accept}
                    onChange={handleInputChange}
                    disabled={disabled}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                />

                <div
                    className={cn(
                        'p-4 rounded-xl mb-4 transition-all duration-300',
                        isDragging ? 'bg-cyan-500/20' : 'bg-white/5'
                    )}
                    style={isDragging ? { boxShadow: theme.glow.cyan } : undefined}
                >
                    <Upload
                        className={cn(
                            'w-10 h-10 transition-colors',
                            isDragging ? 'text-cyan-400' : 'text-gray-400'
                        )}
                    />
                </div>

                <p className="text-lg font-medium text-white mb-2">
                    {isDragging ? 'Dosyayı bırakın' : 'Dosya sürükleyip bırakın'}
                </p>

                <p className="text-sm text-gray-400 mb-4">
                    veya <span className="text-cyan-400 underline">dosya seçin</span>
                </p>

                <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                        <File className="w-4 h-4" />
                        CSV, Excel
                    </span>
                    <span>•</span>
                    <span>Maks. {(maxSize / 1024 / 1024).toFixed(0)}MB</span>
                </div>
            </div>

            {/* Error message */}
            {error && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                    <p className="text-sm text-red-400">{error}</p>
                    <button
                        onClick={() => setError(null)}
                        className="ml-auto cursor-pointer rounded p-1 hover:bg-red-500/20"
                    >
                        <X className="w-4 h-4 text-red-400" />
                    </button>
                </div>
            )}
        </div>
    );
}
