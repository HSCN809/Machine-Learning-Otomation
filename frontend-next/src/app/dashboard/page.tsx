'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
    ArrowRight,
    BarChart3,
    BrainCircuit,
    Database,
    Settings2,
    TrendingUp,
    Upload,
    Zap,
} from 'lucide-react';

import { Header, Sidebar } from '@/components/layout';
import { ProtectedRouteBoundary } from '@/components/auth/ProtectedRouteBoundary';

const features = [
    {
        id: 'upload',
        title: 'Veri Yükleme',
        description: 'CSV, Excel dosyalarınızı yükleyin ve otomatik doğrulama alın',
        icon: Upload,
        href: '/data-upload',
        gradient: 'from-cyan-500 to-blue-500',
        glowColor: 'rgba(0, 217, 255, 0.3)',
    },
    {
        id: 'eda',
        title: 'Keşifsel Analiz',
        description: 'Otomatik EDA, istatistikler ve görselleştirmeler',
        icon: BarChart3,
        href: '/eda',
        gradient: 'from-green-500 to-emerald-500',
        glowColor: 'rgba(0, 255, 136, 0.3)',
    },
    {
        id: 'preprocessing',
        title: 'Veri Ön İşleme',
        description: 'Eksik değerler, outlier, encoding ve scaling işlemleri',
        icon: Settings2,
        href: '/preprocessing',
        gradient: 'from-purple-500 to-pink-500',
        glowColor: 'rgba(168, 85, 247, 0.3)',
    },
    {
        id: 'model',
        title: 'Model Eğitimi',
        description: 'Akıllı model önerisi ve otomatik hiperparametre optimizasyonu',
        icon: BrainCircuit,
        href: '/model',
        gradient: 'from-orange-500 to-red-500',
        glowColor: 'rgba(249, 115, 22, 0.3)',
    },
];

const stats = [
    { label: 'Desteklenen Format', value: '5+', icon: Database },
    { label: 'ML Algoritması', value: '15+', icon: Zap },
    { label: 'Başarı Oranı', value: '%95', icon: TrendingUp },
];

export default function DashboardPage() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

    return (
        <ProtectedRouteBoundary>
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
                    <Header title="Dashboard" />

                    <main className="space-y-8 p-6">
                        <section
                            className="relative overflow-hidden rounded-2xl border border-white/10 p-8"
                            style={{
                                background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.8) 0%, rgba(31, 41, 55, 0.4) 100%)',
                            }}
                        >
                            <div className="absolute inset-0 opacity-30">
                                <div className="absolute right-0 top-0 h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
                                <div className="absolute bottom-0 left-0 h-96 w-96 rounded-full bg-green-500/20 blur-3xl" />
                            </div>

                            <div className="relative z-10">
                                <h1 className="mb-4 text-4xl font-bold">
                                    <span className="text-gradient-primary">ML Automation</span>
                                    <span className="text-white"> ile Başlayın</span>
                                </h1>
                                <p className="mb-6 max-w-2xl text-lg text-gray-400">
                                    Akıllı veri bilimi asistanı ile verilerinizi analiz edin,
                                    ön işleme yapın ve makine öğrenmesi modelleri eğitin.
                                </p>

                                <div className="flex gap-4">
                                    <Link
                                        href="/data-upload"
                                        className="inline-flex items-center gap-2 rounded-xl px-6 py-3 font-medium text-white transition-all duration-200 hover:scale-105"
                                        style={{
                                            background: 'linear-gradient(135deg, #00D9FF 0%, #00FF88 100%)',
                                            boxShadow: '0 0 20px rgba(0, 217, 255, 0.3)',
                                        }}
                                    >
                                        <Upload className="h-5 w-5" />
                                        Veri Yükle
                                        <ArrowRight className="h-4 w-4" />
                                    </Link>

                                    <Link
                                        href="/eda"
                                        className="inline-flex items-center gap-2 rounded-xl border border-white/20 px-6 py-3 font-medium text-white transition-all duration-200 hover:bg-white/5"
                                    >
                                        Daha Fazla Bilgi
                                    </Link>
                                </div>
                            </div>
                        </section>

                        <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
                            {stats.map((stat) => {
                                const Icon = stat.icon;
                                return (
                                    <div
                                        key={stat.label}
                                        className="glass-card flex items-center gap-4 rounded-xl border border-white/10 p-5"
                                    >
                                        <div
                                            className="rounded-lg p-3"
                                            style={{ background: 'linear-gradient(135deg, #00D9FF20 0%, #00FF8820 100%)' }}
                                        >
                                            <Icon className="h-6 w-6 text-cyan-400" />
                                        </div>
                                        <div>
                                            <p className="text-2xl font-bold text-white">{stat.value}</p>
                                            <p className="text-sm text-gray-400">{stat.label}</p>
                                        </div>
                                    </div>
                                );
                            })}
                        </section>

                        <section>
                            <h2 className="mb-4 text-xl font-semibold text-white">Modüller</h2>
                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                {features.map((feature) => {
                                    const Icon = feature.icon;
                                    return (
                                        <Link
                                            key={feature.id}
                                            href={feature.href}
                                            className="group relative overflow-hidden rounded-xl border border-white/10 p-6 transition-all duration-300 hover:border-white/20"
                                            style={{
                                                background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.6) 0%, rgba(31, 41, 55, 0.4) 100%)',
                                            }}
                                        >
                                            <div
                                                className="absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100"
                                                style={{
                                                    background: `radial-gradient(circle at 50% 50%, ${feature.glowColor} 0%, transparent 70%)`,
                                                }}
                                            />

                                            <div className="relative z-10 flex items-start gap-4">
                                                <div
                                                    className={`rounded-xl bg-gradient-to-br p-3 ${feature.gradient}`}
                                                    style={{ boxShadow: `0 0 20px ${feature.glowColor}` }}
                                                >
                                                    <Icon className="h-6 w-6 text-white" />
                                                </div>

                                                <div className="flex-1">
                                                    <h3 className="mb-1 text-lg font-semibold text-white transition-colors group-hover:text-cyan-400">
                                                        {feature.title}
                                                    </h3>
                                                    <p className="text-sm text-gray-400">{feature.description}</p>
                                                </div>

                                                <ArrowRight className="h-5 w-5 text-gray-500 transition-all group-hover:translate-x-1 group-hover:text-cyan-400" />
                                            </div>
                                        </Link>
                                    );
                                })}
                            </div>
                        </section>

                        <section
                            className="rounded-xl border border-cyan-500/20 p-6"
                            style={{
                                background: 'linear-gradient(135deg, rgba(0, 217, 255, 0.05) 0%, rgba(0, 255, 136, 0.05) 100%)',
                            }}
                        >
                            <div className="flex items-start gap-4">
                                <div className="rounded-lg bg-cyan-500/20 p-2">
                                    <Zap className="h-5 w-5 text-cyan-400" />
                                </div>
                                <div>
                                    <h3 className="mb-1 font-semibold text-white">Hızlı Başlangıç</h3>
                                    <p className="text-sm text-gray-400">
                                        <strong className="text-cyan-400">1.</strong> Veri yükleyin →
                                        <strong className="text-cyan-400"> 2.</strong> EDA yapın →
                                        <strong className="text-cyan-400"> 3.</strong> Ön işleme uygulayın →
                                        <strong className="text-cyan-400"> 4.</strong> Model eğitin
                                    </p>
                                </div>
                            </div>
                        </section>
                    </main>
                </div>
            </div>
        </ProtectedRouteBoundary>
    );
}
