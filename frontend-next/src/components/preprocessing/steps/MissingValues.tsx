'use client';

import { useMemo, useState } from 'react';
import { MethodSelector } from '../MethodSelector';
import { ColumnSelector } from '../ColumnSelector';
import { ColumnInfo, MissingValueConfig, MissingValueMethod } from '@/types/preprocessing';
import { Loader2 } from 'lucide-react';
import { theme } from '@/styles/theme';

type MethodCategory = 'numeric' | 'categorical' | 'mixed';

interface MissingValuesProps {
    columnsWithMissing: ColumnInfo[];
    onApply: (config: MissingValueConfig) => Promise<void>;
    isLoading: boolean;
}

const METHODS = [
    { value: 'fill_mean', label: 'Ortalama', icon: '📊', description: 'Sayısal sütunlar için ortalama değer' },
    { value: 'fill_median', label: 'Medyan', icon: '📈', description: 'Sayısal sütunlar için medyan değer' },
    { value: 'fill_mode', label: 'Mod', icon: '📉', description: 'En sık görülen değer' },
    { value: 'fill_knn', label: 'KNN', icon: '🧭', description: 'En yakın komşularla doldur' },
    { value: 'fill_interpolation', label: 'Interpolasyon', icon: '〰️', description: 'Lineer tahmin ile doldur' },
    { value: 'fill_regression', label: 'Regresyon', icon: '📐', description: 'Diğer sütunlardan tahmin et' },
    { value: 'fill_ffill', label: 'Forward Fill', icon: '⬇️', description: 'Önceki değerle doldur' },
    { value: 'fill_bfill', label: 'Backward Fill', icon: '⬆️', description: 'Sonraki değerle doldur' },
    { value: 'drop_columns', label: 'Sütunları Sil', icon: '❌', description: 'Eksik değerli sütunları kaldır' },
];

const METHOD_DETAILS: Record<MissingValueMethod, string> = {
    fill_mean: 'Ortalama ile doldurma, eksik sayısal gözlemleri sütunun aritmetik ortalamasıyla tamamlar. Dağılımı çok bozuk olmayan verilerde pratik ve hızlı bir yaklaşımdır.',
    fill_median: 'Medyan ile doldurma, eksik değerleri ortadaki temsil değeriyle tamamlar. Aykırı değerlerin etkisini ortalamaya göre daha iyi sınırladığı için dayanıklıdır.',
    fill_mode: 'Mod ile doldurma, eksik kayıtları sütunda en sık görülen kategori veya değerle tamamlar. Özellikle kategorik alanlarda veri yapısını korumak için sık kullanılır.',
    fill_knn: 'KNN ile doldurma, eksik sayısal değerleri benzer gözlemlerin değerlerine bakarak tamamlar. Sütunlar arasında ilişki olduğunda ortalama ve medyana göre daha isabetli olabilir.',
    fill_interpolation: 'Interpolasyon, eksik sayısal değerleri komşu gözlemler arasındaki çizgisel ilişkiye göre tahmin eder. Özellikle sıralı veya zaman benzeri verilerde faydalıdır.',
    fill_regression: 'Regresyon tabanlı doldurma, eksik sayısal sütunu diğer sayısal sütunları kullanarak iteratif şekilde tahmin eder. Veri kolonları arasında güçlü ilişki varsa daha zengin sonuç verebilir.',
    fill_ffill: 'Forward fill, eksik kaydı kendisinden önce gelen son geçerli değerle doldurur. Zaman serisi veya sıralı kayıtlarda süreklilik varsayımı yapıldığında kullanışlıdır.',
    fill_bfill: 'Backward fill, eksik değeri kendisinden sonra gelen ilk geçerli gözlemle tamamlar. Gelecek kaydın referans kabul edildiği sıralı veri senaryolarında tercih edilebilir.',
    drop_columns: 'Sütun silme, eksik değer içeren özellikleri tamamen kaldırır. Bilgi değeri düşük veya eksik oranı çok yüksek alanlarda modeli sadeleştirmek için kullanılabilir.',
};

const METHOD_BADGES: Record<
    MissingValueMethod,
    { label: string; tone: 'numeric' | 'categorical' | 'mixed' }
> = {
    fill_mean: { label: 'Sayısal', tone: 'numeric' },
    fill_median: { label: 'Sayısal', tone: 'numeric' },
    fill_mode: { label: 'Kategorik', tone: 'categorical' },
    fill_knn: { label: 'Sayısal', tone: 'numeric' },
    fill_interpolation: { label: 'Sayısal', tone: 'numeric' },
    fill_regression: { label: 'Sayısal', tone: 'numeric' },
    fill_ffill: { label: 'Ortak', tone: 'mixed' },
    fill_bfill: { label: 'Ortak', tone: 'mixed' },
    drop_columns: { label: 'Ortak', tone: 'mixed' },
};

const METHOD_DETAILS_MARKDOWN: Record<MissingValueMethod, string> = {
    fill_mean: '**Ne yapar?** Eksik sayısal gözlemleri sütunun aritmetik ortalamasıyla tamamlar.\n\n**Ne zaman uygundur?** Dağılımı çok bozuk olmayan verilerde pratik ve hızlı bir yaklaşımdır.',
    fill_median: '**Ne yapar?** Eksik değerleri ortadaki temsil değeriyle tamamlar.\n\n**Ne zaman uygundur?** Aykırı değerlerin etkisini ortalamaya göre daha iyi sınırladığı için dayanıklı bir seçenektir.',
    fill_mode: '**Ne yapar?** Eksik kayıtları sütunda en sık görülen kategori veya değerle tamamlar.\n\n**Ne zaman uygundur?** Özellikle kategorik alanlarda veri yapısını korumak için sık kullanılır.',
    fill_knn: '**Ne yapar?** Eksik sayısal değerleri en yakın komşu gözlemlere göre doldurur.\n\n**Ne zaman uygundur?** Sayısal sütunlar birbiriyle ilişkiliyse basit ortalama yöntemlerine göre daha iyi sonuç verebilir.',
    fill_interpolation: '**Ne yapar?** Eksik sayısal değerleri komşu gözlemler arasındaki çizgisel akışa göre tahmin eder.\n\n**Ne zaman uygundur?** Sıralı veri, trend içeren kolonlar ve zaman benzeri kayıtlar için uygundur.',
    fill_regression: '**Ne yapar?** Eksik sayısal sütunu diğer sayısal sütunları kullanarak iteratif regresyon yaklaşımıyla tahmin eder.\n\n**Ne zaman uygundur?** Kolonlar arasında güçlü ilişki varsa gelişmiş bir alternatif olarak kullanılabilir.',
    fill_ffill: '**Ne yapar?** Eksik kaydı kendisinden önce gelen son geçerli değerle doldurur.\n\n**Ne zaman uygundur?** Zaman serisi veya sıralı kayıtlarda süreklilik varsayımı yapıldığında tercih edilir.',
    fill_bfill: '**Ne yapar?** Eksik değeri kendisinden sonra gelen ilk geçerli gözlemle tamamlar.\n\n**Ne zaman uygundur?** Gelecek kaydın referans kabul edildiği sıralı veri senaryolarında kullanılabilir.',
    drop_columns: '**Ne yapar?** Eksik değer içeren özellikleri tamamen kaldırır.\n\n**Ne zaman uygundur?** Bilgi değeri düşük veya eksik oranı çok yüksek alanlarda modeli sadeleştirmek için kullanılabilir.',
};

export function MissingValues({ columnsWithMissing, onApply, isLoading }: MissingValuesProps) {
    const [method, setMethod] = useState<MissingValueMethod>('fill_mean');
    const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
    const [activeCategory, setActiveCategory] = useState<MethodCategory>('numeric');

    const filteredMethods = useMemo(
        () =>
            METHODS.filter((option) => {
                const tone = METHOD_BADGES[option.value as MissingValueMethod].tone;
                if (activeCategory === 'numeric') {
                    return tone === 'numeric';
                }
                if (activeCategory === 'categorical') {
                    return tone === 'categorical';
                }

                return tone === 'mixed';
            }),
        [activeCategory]
    );

    const handleApply = async () => {
        if (selectedColumns.length === 0) return;

        await onApply({
            method,
            columns: selectedColumns,
        });

        // Reset after apply
        setSelectedColumns([]);
    };

    const canApply = selectedColumns.length > 0;

    return (
        <div className="space-y-6">
            {/* Method selector */}
            <MethodSelector
                label="Doldurma Yöntemi"
                headerContent={
                    <div className="flex w-fit items-center gap-6 border-b border-white/10 pb-0">
                        {[
                            { key: 'numeric' as const, label: 'Sayısal' },
                            { key: 'categorical' as const, label: 'Kategorik' },
                            { key: 'mixed' as const, label: 'Ortak' },
                        ].map((category) => {
                            const isActive = activeCategory === category.key;
                            const categoryMethods = METHODS.filter((option) => {
                                const tone = METHOD_BADGES[option.value as MissingValueMethod].tone;
                                if (category.key === 'numeric') {
                                    return tone === 'numeric';
                                }
                                if (category.key === 'categorical') {
                                    return tone === 'categorical';
                                }

                                return tone === 'mixed';
                            });

                            return (
                                <button
                                    key={category.key}
                                    type="button"
                                    onClick={() => {
                                        setActiveCategory(category.key);
                                        if (!categoryMethods.some((option) => option.value === method) && categoryMethods.length > 0) {
                                            setMethod(categoryMethods[0].value as MissingValueMethod);
                                        }
                                    }}
                                    disabled={isLoading}
                                    className={`relative shrink-0 pb-1 text-sm font-medium transition-colors duration-200 ${
                                        isLoading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
                                    } ${isActive ? 'text-white' : 'text-gray-400 hover:text-gray-200'}`}
                                >
                                    {category.label}
                                    <span
                                        className={`absolute inset-x-0 -bottom-px z-10 h-0.5 rounded-full transition-opacity duration-200 ${
                                            isActive ? 'opacity-100' : 'opacity-0'
                                        }`}
                                        style={{
                                            background: theme.gradients.primary,
                                            boxShadow: isActive ? theme.glow.cyan : undefined,
                                        }}
                                    />
                                </button>
                            );
                        })}
                    </div>
                }
                options={filteredMethods.map((option) => ({
                    ...option,
                    badgeLabel: METHOD_BADGES[option.value as MissingValueMethod].label,
                    badgeTone: METHOD_BADGES[option.value as MissingValueMethod].tone,
                    details:
                        METHOD_DETAILS_MARKDOWN[option.value as MissingValueMethod]
                        ?? METHOD_DETAILS[option.value as MissingValueMethod],
                }))}
                value={method}
                onChange={(v) => setMethod(v as MissingValueMethod)}
                disabled={isLoading}
            />
            {/* Column selector */}
            <ColumnSelector
                columns={columnsWithMissing}
                selectedColumns={selectedColumns}
                onChange={setSelectedColumns}
                label="Uygulanacak Sütunları Seç"
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
}
