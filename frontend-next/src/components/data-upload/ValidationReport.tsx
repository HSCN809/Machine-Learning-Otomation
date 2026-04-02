'use client';

import { AlertTriangle, AlertCircle, Info, CheckCircle, Sparkles, Loader2, RotateCcw, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { theme } from '@/styles/theme';
import { ValidationReport as ValidationReportType, ValidationIssue } from '@/types/data-upload';
import { IssueCard } from './IssueCard';

interface ValidationReportProps {
    report: ValidationReportType;
    onEnhanceWithLLM?: () => Promise<void>;
    onResetLLMSuggestions?: () => void;
    onDelete?: () => void | Promise<void>;
    isEnhancing?: boolean;
    hasLLMSuggestions?: boolean;
}

export function ValidationReport({
    report,
    onEnhanceWithLLM,
    onResetLLMSuggestions,
    onDelete,
    isEnhancing = false,
    hasLLMSuggestions = false,
}: ValidationReportProps) {
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
                <div className="flex items-start justify-between gap-4">
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

                    {onDelete && (
                        <button
                            onClick={onDelete}
                            className="flex items-center gap-2 px-3 py-2 rounded-xl border border-white/10 text-gray-400 hover:text-white hover:bg-white/5 transition-all cursor-pointer"
                        >
                            <Trash2 className="w-4 h-4" />
                            <span>Sil</span>
                        </button>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between gap-4">
                <h3 className="text-lg font-semibold text-white">Doğrulama Raporu</h3>
                <div className="flex items-center gap-3 text-sm">
                    <div className="flex items-center gap-4">
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

                    {onDelete && (
                        <button
                            onClick={onDelete}
                            className="flex items-center gap-2 px-3 py-2 rounded-xl border border-white/10 text-gray-400 hover:text-white hover:bg-white/5 transition-all cursor-pointer"
                        >
                            <Trash2 className="w-4 h-4" />
                            <span>Sil</span>
                        </button>
                    )}
                </div>
            </div>

            {onEnhanceWithLLM && !hasLLMSuggestions && (
                <button
                    onClick={onEnhanceWithLLM}
                    disabled={isEnhancing}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-white transition-all hover:scale-[1.02] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                        background: theme.gradients.primary,
                        boxShadow: theme.glow.cyan,
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
                            <span>LLM ile Akıllı Öneriler Al</span>
                        </>
                    )}
                </button>
            )}

            {hasLLMSuggestions && (
                <div className="flex items-center justify-between px-4 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-cyan-400" />
                        <span className="text-sm text-cyan-300">
                            LLM önerileri yüklendi, sorunlara tıklayarak görüntüleyin
                        </span>
                    </div>
                    {onResetLLMSuggestions && (
                        <button
                            onClick={onResetLLMSuggestions}
                            className="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-white rounded hover:bg-white/10 transition-colors"
                        >
                            <RotateCcw className="w-3 h-3" />
                            Sıfırla
                        </button>
                    )}
                </div>
            )}

            {issuesBySeverity.critical.length > 0 && (
                <IssueSection
                    title={severityConfig.critical.label}
                    issues={issuesBySeverity.critical}
                    config={severityConfig.critical}
                />
            )}

            {issuesBySeverity.warning.length > 0 && (
                <IssueSection
                    title={severityConfig.warning.label}
                    issues={issuesBySeverity.warning}
                    config={severityConfig.warning}
                />
            )}

            {issuesBySeverity.info.length > 0 && (
                <IssueSection
                    title={severityConfig.info.label}
                    issues={issuesBySeverity.info}
                    config={severityConfig.info}
                />
            )}

            <p className="text-sm text-gray-500">
                Bu sorunlar bilgilendirme amaçlıdır. Düzeltme işlemleri &apos;Veri Ön İşleme&apos; modülünde yapılabilir.
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
