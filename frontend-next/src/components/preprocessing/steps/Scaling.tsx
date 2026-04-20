'use client';

import { useState } from 'react';
import { MethodSelector } from '../MethodSelector';
import { ColumnSelector } from '../ColumnSelector';
import { ColumnInfo, ScalingConfig, ScalingMethod } from '@/types/preprocessing';
import { Loader2 } from 'lucide-react';
import { theme } from '@/styles/theme';

interface ScalingProps {
    numericColumns: ColumnInfo[];
    onApply: (config: ScalingConfig) => Promise<void>;
    isLoading: boolean;
}

const METHODS = [
    { value: 'standard', label: 'Standard Scaler', icon: '📐', description: 'Ortalama 0, std 1 olacak şekilde' },
    { value: 'minmax', label: 'MinMax Scaler', icon: '📏', description: '0-1 aralığına dönüştür' },
    { value: 'robust', label: 'Robust Scaler', icon: '🛡️', description: 'Aykırı değerlere dayanıklı' },
    { value: 'maxabs', label: 'MaxAbs Scaler', icon: '📊', description: '-1 ile 1 arasına ölçekle' },
    { value: 'normalizer', label: 'Normalizer', icon: '🔄', description: 'Birim norm\'a normalize et' },
];

const METHOD_DETAILS_MARKDOWN: Record<ScalingMethod, string> = {
    standard:
        '**Ne yapar?** Her sütunu ortalaması 0 ve standart sapması 1 olacak şekilde dönüştürür.\n\n**Ne zaman uygundur?** Özellikle uzaklık/gradient tabanlı modellerde ölçek farkını azaltmak için kullanılır.',
    minmax:
        '**Ne yapar?** Değerleri belirlenen aralığa (genelde 0-1) lineer olarak taşır.\n\n**Ne zaman uygundur?** Özelliklerin aynı bantta olmasının önemli olduğu modellerde pratik bir tercihtir.',
    robust:
        '**Ne yapar?** Medyan ve IQR kullanarak ölçekler, uç değerlere daha az duyarlıdır.\n\n**Ne zaman uygundur?** Aykırı değerlerin yoğun olduğu veri setlerinde daha stabil sonuç verir.',
    maxabs:
        '**Ne yapar?** Her sütunu mutlak maksimum değerine bölerek aralığı yaklaşık -1 ile 1’e getirir.\n\n**Ne zaman uygundur?** Seyrek veri yapısını bozmadan ölçekleme gerektiğinde tercih edilir.',
    normalizer:
        '**Ne yapar?** Her satırı seçilen norma göre birim vektöre dönüştürür.\n\n**Ne zaman uygundur?** Yön bilgisinin büyüklükten daha önemli olduğu metin/vektör benzerliği problemlerinde faydalıdır.',
};

import React from 'react';

export const Scaling = React.memo(function Scaling({ numericColumns, onApply, isLoading }: ScalingProps) {
    const [method, setMethod] = useState<ScalingMethod>('standard');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);

    const handleApply = async () => {
        if (selectedColumns.length === 0) return;

        await onApply({
            method,
            columns: selectedColumns,
        });

        setSelectedColumns([]);
    };

    const canApply = selectedColumns.length > 0;

    return (
        <div className="space-y-6">

            {/* Method selector */}
            <MethodSelector
                label="Ölçeklendirme Yöntemi"
                options={METHODS.map((option) => ({
                    ...option,
                    details: METHOD_DETAILS_MARKDOWN[option.value as ScalingMethod],
                }))}
                value={method}
                onChange={(v) => setMethod(v as ScalingMethod)}
                disabled={isLoading}
            />

            {/* Column selector */}
            <ColumnSelector
                columns={numericColumns}
                selectedColumns={selectedColumns}
                onChange={setSelectedColumns}
                label="Uygulanacak Sayısal Sütunlar"
                showMissing={false}
                disabled={isLoading}
            />

            {/* Apply button */}
            <button
                onClick={handleApply}
                disabled={!canApply || isLoading}
                className={`w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-medium text-white transition-all duration-200 ${
                    !canApply || isLoading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
                }`}
                style={{
                    background: canApply && !isLoading ? theme.gradients.primary : 'rgba(255,255,255,0.1)',
                    boxShadow: canApply && !isLoading ? theme.glow.cyan : undefined,
                }}
            >
                {isLoading ? (
                    <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        İşleniyor...
                    </>
                ) : (
                    <>Uygula</>
                )}
            </button>
        </div>
    );
});
