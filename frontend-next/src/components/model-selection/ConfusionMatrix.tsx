'use client';



interface ConfusionMatrixProps {
    matrix: number[][];
    labels?: string[];
}

export function ConfusionMatrix({ matrix, labels = ['0', '1'] }: ConfusionMatrixProps) {
    const total = matrix.flat().reduce((sum, val) => sum + val, 0);
    const maxValue = Math.max(...matrix.flat());

    const getColor = (value: number, row: number, col: number) => {
        const intensity = value / maxValue;
        // Diagonal (correct predictions) = green, off-diagonal = red
        if (row === col) {
            return `rgba(0, 255, 136, ${intensity * 0.6 + 0.1})`;
        }
        return `rgba(239, 68, 68, ${intensity * 0.6 + 0.1})`;
    };

    return (
        <div className="p-6 rounded-xl border border-white/10 bg-white/5">
            <h4 className="font-semibold text-white mb-4">Confusion Matrix</h4>

            <div className="flex flex-col items-center">
                {/* Column labels */}
                <div className="flex mb-2">
                    <div className="w-16" /> {/* Spacer for row labels */}
                    {labels.map((label, i) => (
                        <div
                            key={`col-${i}`}
                            className="w-20 text-center text-sm text-gray-400"
                        >
                            Tahmin: {label}
                        </div>
                    ))}
                </div>

                {/* Matrix rows */}
                {matrix.map((row, i) => (
                    <div key={`row-${i}`} className="flex items-center">
                        {/* Row label */}
                        <div className="w-16 text-sm text-gray-400 text-right pr-3">
                            Gerçek: {labels[i]}
                        </div>

                        {/* Cells */}
                        {row.map((value, j) => (
                            <div
                                key={`cell-${i}-${j}`}
                                className="w-20 h-16 flex flex-col items-center justify-center rounded-lg m-1 transition-all hover:scale-105"
                                style={{
                                    backgroundColor: getColor(value, i, j),
                                }}
                            >
                                <span className="text-lg font-bold text-white">{value}</span>
                                <span className="text-xs text-white/70">
                                    {((value / total) * 100).toFixed(1)}%
                                </span>
                            </div>
                        ))}
                    </div>
                ))}
            </div>

            {/* Legend */}
            <div className="flex items-center justify-center gap-6 mt-4 text-xs text-gray-400">
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(0, 255, 136, 0.5)' }} />
                    <span>Doğru Tahmin</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(239, 68, 68, 0.5)' }} />
                    <span>Yanlış Tahmin</span>
                </div>
            </div>
        </div>
    );
}
