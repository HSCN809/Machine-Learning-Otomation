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
import { NoDataWarning, SessionPageSkeleton, StepProgress } from '@/components/common';
import { useEDA } from '@/hooks/useEDA';
import { hasStoredSession } from '@/lib/api';
import { BarChart3, TrendingUp, GitBranch, Layers } from 'lucide-react';

type TabId = 'summary' | 'numeric' | 'correlation' | 'categorical';

const tabs = [
    {
        id: 'summary' as TabId,
        label: 'Özet',
        icon: <BarChart3 className="w-5 h-5" />,
    },
    {
        id: 'numeric' as TabId,
        label: 'Sayısal Analiz',
        icon: <TrendingUp className="w-5 h-5" />,
    },
    {
        id: 'correlation' as TabId,
        label: 'Korelasyon',
        icon: <GitBranch className="w-5 h-5" />,
    },
    {
        id: 'categorical' as TabId,
        label: 'Kategorik',
        icon: <Layers className="w-5 h-5" />,
    },
];

const chartSelectClassName =
    'min-w-[160px] rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-cyan-500/50';

export default function EDAPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [activeTab, setActiveTab] = useState<TabId>('summary');
    const [hasSession] = useState(() => hasStoredSession());

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

    const activeTabIndex = tabs.findIndex((tab) => tab.id === activeTab);

    useEffect(() => {
        if (hasSession) {
            loadEDAData();
        }
    }, [hasSession, loadEDAData]);

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
                <Header
                    title="Keşifsel Veri Analizi (EDA)"
                    subtitle="Verilerinizi analiz edin, istatistikleri görüntüleyin ve görselleştirmeler oluşturun."
                />

                <main className="p-6 space-y-6">
                    {hasSession === true && isLoading && !edaData && <SessionPageSkeleton variant="analytics" />}

                    {!isLoading && hasSession !== null && !edaData && (
                        <NoDataWarning
                            title="Veri Yüklenmedi"
                            description="Keşifsel veri analizi yapabilmek için önce veri yüklemeniz gerekmektedir."
                        />
                    )}

                    {edaData && !isLoading && (
                        <>
                            <StepProgress
                                steps={tabs.map((tab) => ({
                                    id: tab.id,
                                    name: tab.label,
                                    icon: tab.icon,
                                }))}
                                currentStep={activeTabIndex}
                                onStepClick={(step) => setActiveTab(tabs[step].id)}
                                isStepClickable={() => true}
                                showActiveLine={false}
                            />

                            {activeTab === 'summary' && (
                                <div className="space-y-6">
                                    <StatsSummary
                                        numericStats={edaData.numericStats}
                                        categoricalStats={edaData.categoricalStats}
                                        columnTypes={edaData.columnTypes}
                                        duplicateRows={edaData.duplicateRows}
                                    />
                                    <DataTypesTable columnTypes={edaData.columnTypes} />
                                </div>
                            )}

                            {activeTab === 'numeric' && selectedNumericColumn && (
                                <div className="space-y-6">
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
                                                                          <label className="text-sm text-gray-400">
                                                                              Sütun Seç:
                                                                          </label>
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

                            {activeTab === 'categorical' && selectedCategoricalColumn && (
                                <div className="space-y-6">
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
                                                                    onChange={(e) =>
                                                                        setSelectedCategoricalColumn(e.target.value)
                                                                    }
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
                                                                    onChange={(e) =>
                                                                        setSelectedCategoricalColumn(e.target.value)
                                                                    }
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
                                </div>
                            )}
                        </>
                    )}
                </main>
            </div>
        </div>
    );
}
