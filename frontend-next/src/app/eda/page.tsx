'use client';

import { useState, useEffect } from 'react';
import { Sidebar, Header } from '@/components/layout';
import {
    ChartCarousel,
    StatsSummary,
    DataTypesTable,
    HistogramChart,
    BoxPlotChart,
    ScatterChart,
    CorrelationMatrix,
    CategoryDistribution,
} from '@/components/eda';
import { NoDataWarning } from '@/components/common';
import { useEDA } from '@/hooks/useEDA';
import { hasStoredSession } from '@/lib/api';
import { theme } from '@/styles/theme';
import { Loader2, BarChart3, TrendingUp, GitBranch, Layers } from 'lucide-react';

type TabId = 'summary' | 'numeric' | 'correlation' | 'categorical';

const tabs: { id: TabId; label: string; icon: React.ElementType }[] = [
    { id: 'summary', label: 'Özet', icon: BarChart3 },
    { id: 'numeric', label: 'Sayısal Analiz', icon: TrendingUp },
    { id: 'correlation', label: 'Korelasyon', icon: GitBranch },
    { id: 'categorical', label: 'Kategorik', icon: Layers },
];

const chartSelectClassName =
    'min-w-[160px] rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-cyan-500/50';

export default function EDAPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [activeTab, setActiveTab] = useState<TabId>('summary');
    const [hasSession, setHasSession] = useState<boolean | null>(null);

    const {
        edaData,
        isLoading,
        selectedNumericColumn,
        selectedCategoricalColumn,
        setSelectedNumericColumn,
        setSelectedCategoricalColumn,
        loadEDAData,
        histogramData,
        boxPlotData,
        categoryData,
        scatterData,
        scatterXColumn,
        scatterYColumn,
        setScatterColumns,
    } = useEDA();

    useEffect(() => {
        const sessionExists = hasStoredSession();
        setHasSession(sessionExists);

        if (sessionExists) {
            loadEDAData();
        }
    }, [loadEDAData]);

    return (
        <div className="min-h-screen">
            <Sidebar
                isCollapsed={sidebarCollapsed}
                onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
            />

            <div
                className="transition-all duration-300"
                style={{
                    marginLeft: sidebarCollapsed ? '80px' : '288px',
                }}
            >
                <Header title="Keşifsel Veri Analizi (EDA)" />

                <main className="p-6 space-y-6">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-2">Keşifsel Veri Analizi</h1>
                        <p className="text-gray-400">
                            Verilerinizi analiz edin, istatistikleri görüntüleyin ve görselleştirmeler oluşturun.
                        </p>
                    </div>

                    {isLoading && (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
                            <span className="ml-3 text-gray-400">Veriler analiz ediliyor...</span>
                        </div>
                    )}

                    {!isLoading && hasSession !== null && !edaData && (
                        <NoDataWarning
                            title="Veri Yüklenmedi"
                            description="Keşifsel veri analizi yapabilmek için önce veri yüklemeniz gerekmektedir."
                        />
                    )}

                    {edaData && !isLoading && (
                        <>
                            <div className="flex gap-2 border-b border-white/10 pb-2">
                                {tabs.map((tab) => {
                                    const Icon = tab.icon;
                                    const isActive = activeTab === tab.id;

                                    return (
                                        <button
                                            key={tab.id}
                                            onClick={() => setActiveTab(tab.id)}
                                            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 cursor-pointer ${
                                                isActive
                                                    ? 'text-white'
                                                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                                            }`}
                                            style={
                                                isActive
                                                    ? {
                                                          background: `${theme.colors.primary.cyan}20`,
                                                          boxShadow: `0 0 10px ${theme.colors.primary.cyan}30`,
                                                      }
                                                    : undefined
                                            }
                                        >
                                            <Icon className="w-4 h-4" />
                                            {tab.label}
                                        </button>
                                    );
                                })}
                            </div>

                            {activeTab === 'summary' && (
                                <div className="space-y-6">
                                    <StatsSummary
                                        numericStats={edaData.numericStats}
                                        categoricalStats={edaData.categoricalStats}
                                        columnTypes={edaData.columnTypes}
                                    />
                                    <DataTypesTable columnTypes={edaData.columnTypes} />
                                </div>
                            )}

                            {activeTab === 'numeric' && (
                                <div className="space-y-6">
                                    {selectedNumericColumn && (
                                        <ChartCarousel
                                            slides={[
                                                {
                                                    id: 'histogram',
                                                    label: 'Histogram',
                                                    content: (
                                                        <HistogramChart
                                                            data={histogramData}
                                                            column={selectedNumericColumn}
                                                            headerActions={
                                                                <>
                                                                    <label className="text-sm text-gray-400">Sütun Seç:</label>
                                                                    <select
                                                                        value={selectedNumericColumn}
                                                                        onChange={(e) => setSelectedNumericColumn(e.target.value)}
                                                                        className={chartSelectClassName}
                                                                        aria-label="Histogram sütunu seç"
                                                                    >
                                                                        {edaData.numericColumns.map((col) => (
                                                                            <option key={col} value={col} className="bg-gray-800">
                                                                                {col}
                                                                            </option>
                                                                        ))}
                                                                    </select>
                                                                </>
                                                            }
                                                        />
                                                    ),
                                                },
                                                ...(boxPlotData
                                                    ? [
                                                          {
                                                              id: 'boxplot',
                                                              label: 'Box Plot',
                                                              content: (
                                                                  <BoxPlotChart
                                                                      data={boxPlotData}
                                                                      column={selectedNumericColumn}
                                                                      headerActions={
                                                                          <>
                                                                              <label className="text-sm text-gray-400">Sütun Seç:</label>
                                                                              <select
                                                                                  value={selectedNumericColumn}
                                                                                  onChange={(e) =>
                                                                                      setSelectedNumericColumn(e.target.value)
                                                                                  }
                                                                                  className={chartSelectClassName}
                                                                                  aria-label="Box plot sütunu seç"
                                                                              >
                                                                                  {edaData.numericColumns.map((col) => (
                                                                                      <option
                                                                                          key={col}
                                                                                          value={col}
                                                                                          className="bg-gray-800"
                                                                                      >
                                                                                          {col}
                                                                                      </option>
                                                                                  ))}
                                                                              </select>
                                                                          </>
                                                                      }
                                                                  />
                                                              ),
                                                          },
                                                      ]
                                                    : []),
                                            ]}
                                        />
                                    )}
                                </div>
                            )}

                            {activeTab === 'correlation' && (
                                <ChartCarousel
                                    slides={[
                                        {
                                            id: 'correlation-matrix',
                                            label: 'Korelasyon Matrisi',
                                            content: (
                                                <CorrelationMatrix
                                                    data={edaData.correlationMatrix}
                                                    columns={edaData.numericColumns}
                                                />
                                            ),
                                        },
                                        {
                                            id: 'scatter-plot',
                                            label: 'Scatter Plot',
                                            content:
                                                scatterXColumn && scatterYColumn ? (
                                                    <ScatterChart
                                                        data={scatterData}
                                                        xColumn={scatterXColumn}
                                                        yColumn={scatterYColumn}
                                                        headerActions={
                                                            <>
                                                                <label className="text-sm text-gray-400">X Ekseni:</label>
                                                                <select
                                                                    value={scatterXColumn}
                                                                    onChange={(e) =>
                                                                        setScatterColumns(e.target.value, scatterYColumn)
                                                                    }
                                                                    className={chartSelectClassName}
                                                                    aria-label="Scatter X ekseni seç"
                                                                >
                                                                    {edaData.numericColumns.map((col) => (
                                                                        <option
                                                                            key={col}
                                                                            value={col}
                                                                            className="bg-gray-800"
                                                                            disabled={col === scatterYColumn}
                                                                        >
                                                                            {col}
                                                                        </option>
                                                                    ))}
                                                                </select>
                                                                <label className="text-sm text-gray-400">Y Ekseni:</label>
                                                                <select
                                                                    value={scatterYColumn}
                                                                    onChange={(e) =>
                                                                        setScatterColumns(scatterXColumn, e.target.value)
                                                                    }
                                                                    className={chartSelectClassName}
                                                                    aria-label="Scatter Y ekseni seç"
                                                                >
                                                                    {edaData.numericColumns.map((col) => (
                                                                        <option
                                                                            key={col}
                                                                            value={col}
                                                                            className="bg-gray-800"
                                                                            disabled={col === scatterXColumn}
                                                                        >
                                                                            {col}
                                                                        </option>
                                                                    ))}
                                                                </select>
                                                            </>
                                                        }
                                                    />
                                                ) : null,
                                        },
                                    ]}
                                />
                            )}

                            {activeTab === 'categorical' && (
                                <div className="space-y-6">
                                    {selectedCategoricalColumn && (
                                        <ChartCarousel
                                            slides={[
                                                {
                                                    id: 'category-bar',
                                                    label: 'Çubuk Grafik',
                                                    content: (
                                                        <CategoryDistribution
                                                            data={categoryData}
                                                            column={selectedCategoricalColumn}
                                                            chartType="bar"
                                                            headerActions={
                                                                <>
                                                                    <label className="text-sm text-gray-400">Sütun Seç:</label>
                                                                    <select
                                                                        value={selectedCategoricalColumn}
                                                                        onChange={(e) => setSelectedCategoricalColumn(e.target.value)}
                                                                        className={chartSelectClassName}
                                                                        aria-label="Kategorik çubuk grafik sütunu seç"
                                                                    >
                                                                        {edaData.categoricalColumns.map((col) => (
                                                                            <option key={col} value={col} className="bg-gray-800">
                                                                                {col}
                                                                            </option>
                                                                        ))}
                                                                    </select>
                                                                </>
                                                            }
                                                        />
                                                    ),
                                                },
                                                {
                                                    id: 'category-pie',
                                                    label: 'Pasta Grafik',
                                                    content: (
                                                        <CategoryDistribution
                                                            data={categoryData}
                                                            column={selectedCategoricalColumn}
                                                            chartType="pie"
                                                            headerActions={
                                                                <>
                                                                    <label className="text-sm text-gray-400">Sütun Seç:</label>
                                                                    <select
                                                                        value={selectedCategoricalColumn}
                                                                        onChange={(e) => setSelectedCategoricalColumn(e.target.value)}
                                                                        className={chartSelectClassName}
                                                                        aria-label="Kategorik pasta grafik sütunu seç"
                                                                    >
                                                                        {edaData.categoricalColumns.map((col) => (
                                                                            <option key={col} value={col} className="bg-gray-800">
                                                                                {col}
                                                                            </option>
                                                                        ))}
                                                                    </select>
                                                                </>
                                                            }
                                                        />
                                                    ),
                                                },
                                            ]}
                                        />
                                    )}
                                </div>
                            )}

                            <div
                                className="p-6 rounded-xl border border-cyan-500/20"
                                style={{
                                    background:
                                        'linear-gradient(135deg, rgba(0, 217, 255, 0.05) 0%, rgba(0, 255, 136, 0.05) 100%)',
                                }}
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="font-semibold text-white mb-1">Sonraki Adım</h3>
                                        <p className="text-sm text-gray-400">
                                            Verilerinizi ön işleme adımlarından geçirin.
                                        </p>
                                    </div>
                                    <a
                                        href="/preprocessing"
                                        className="px-4 py-2 rounded-xl font-medium text-white transition-all hover:scale-105"
                                        style={{
                                            background: theme.gradients.primary,
                                            boxShadow: theme.glow.cyan,
                                        }}
                                    >
                                        Ön İşleme
                                    </a>
                                </div>
                            </div>
                        </>
                    )}
                </main>
            </div>
        </div>
    );
}
