'use client';

import { useState } from 'react';
import { AlertTriangle, AlertCircle, Info, CheckCircle, Sparkles, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme'
import { ValidationReport as ValidationReportType, ValidationIssue } from '@/types/data-upload';
import { IssueCard } from './IssueCard';

interface ValidationReportProps {
    report: ValidationReportType;
    onEnhanceWithLLM?: () => Promise<void>;
    isEnhancing?: boolean;
    hasLLMSuggestions?: boolean;
}

export function ValidationReport({ report, onEnhanceWithLLM, isEnhancing = false, hasLLMSuggestions = false }: ValidationReportProps) {
    const { totalIssues, issuesBySeverity } = report;

    const severityConfig = {
        critical: {
            icon: AlertCircle,
            label: 'Kritik Sorunlar',
            color: theme.colors.status.error,
            bgColor: 'bg-red-500/10',
            borderColor: 'border-red-500/30',
        },
        warning: {
            icon: AlertTriangle,
            label: 'Uyarılar',
            color: theme.colors.status.warning,
            bgColor: 'bg-yellow-500/10',
            borderColor: 'border-yellow-500/30',
        },
        info: {
            icon: Info,
            label: 'Bilgilendirmeler',
            color: theme.colors.status.info,
            bgColor: 'bg-blue-500/10',
            borderColor: 'border-blue-500/30',
        },
    };

    if (totalIssues === 0) {
        return (
            <div className="p-6 rounded-xl border border-green-500/30 bg-green-500/5">
                <div className="flex items-center gap-3">
                    <div
                        className="p-3 rounded-lg"
                        style={{
                            background: `${theme.colors.status.success}20`,
                            boxShadow: `0 0 15px ${theme.colors.status.success}30`,
                        }}
                    >
                        <CheckCircle className="w-6 h-6 text-green-400" />
                    </div>
                    <div>
                        <p className="font-semibold text-white">Veri kalitesi iyi görünüyor!</p>
                        <p className="text-sm text-gray-400">Tespit edilen sorun yok.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Summary */}
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Doğrulama Raporu</h3>
                <div className="flex items-center gap-4 text-sm">
                    {issuesBySeverity.critical.length > 0 && (
                        <span className="flex items-center gap-1 text-red-400">
                            <AlertCircle className="w-4 h-4" />
                            {issuesBySeverity.critical.length} kritik
                        </span>
                    )}
                    {issuesBySeverity.warning.length > 0 && (
                        <span className="flex items-center gap-1 text-yellow-400">
                            <AlertTriangle className="w-4 h-4" />
                            {issuesBySeverity.warning.length} uyarı
                        </span>
                    )}
                    {issuesBySeverity.info.length > 0 && (
                        <span className="flex items-center gap-1 text-blue-400">
                            <Info className="w-4 h-4" />
                            {issuesBySeverity.info.length} bilgi
                        </span>
                    )}
                </div>
            </div>

            {/* LLM Enhancement Button */}
            {onEnhanceWithLLM && !hasLLMSuggestions && (
                <button
                    onClick={onEnhanceWithLLM}
                    disabled={isEnhancing}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-white transition-all hover:scale-[1.02] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                        background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
                        boxShadow: '0 0 20px rgba(139, 92, 246, 0.3)',
                    }}
                >
                    {isEnhancing ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            <span>LLM analiz ediyor...</span>
                        </>
                    ) : (
                        <>
                            <Sparkles className="w-5 h-5" />
                            <span>🤖 LLM ile Akıllı Öneriler Al</span>
                        </>
                    )}
                </button>
            )}

            {hasLLMSuggestions && (
                <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/10 border border-purple-500/30">
                    <Sparkles className="w-4 h-4 text-purple-400" />
                    <span className="text-sm text-purple-300">LLM önerileri yüklendi - sorunlara tıklayarak görüntüleyin</span>
                </div>
            )}

            {/* Critical issues */}
            {issuesBySeverity.critical.length > 0 && (
                <IssueSection
                    title={severityConfig.critical.label}
                    issues={issuesBySeverity.critical}
                    config={severityConfig.critical}
                />
            )}

            {/* Warnings */}
            {issuesBySeverity.warning.length > 0 && (
                <IssueSection
                    title={severityConfig.warning.label}
                    issues={issuesBySeverity.warning}
                    config={severityConfig.warning}
                />
            )}

            {/* Info */}
            {issuesBySeverity.info.length > 0 && (
                <IssueSection
                    title={severityConfig.info.label}
                    issues={issuesBySeverity.info}
                    config={severityConfig.info}
                />
            )}

            {/* Note */}
            <p className="text-sm text-gray-500">
                💡 Bu sorunlar bilgilendirme amaçlıdır. Düzeltme işlemleri &apos;Veri Ön İşleme&apos; modülünde yapılabilir.
            </p>
        </div>
    );
}

interface IssueSectionProps {
    title: string;
    issues: ValidationIssue[];
    config: {
        icon: React.ElementType;
        color: string;
        bgColor: string;
        borderColor: string;
    };
}

function IssueSection({ title, issues, config }: IssueSectionProps) {
    const Icon = config.icon;

    return (
        <div className={cn('rounded-xl border p-4', config.bgColor, config.borderColor)}>
            <div className="flex items-center gap-2 mb-3">
                <Icon className="w-5 h-5" style={{ color: config.color }} />
                <span className="font-medium" style={{ color: config.color }}>
                    {title}
                </span>
            </div>
            <div className="space-y-2">
                {issues.map((issue) => (
                    <IssueCard key={issue.id} issue={issue} />
                ))}
            </div>
        </div>
    );
}
