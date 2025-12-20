'use client';

import { ChevronDown, ChevronUp, Lightbulb } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { ValidationIssue } from '@/types/data-upload';

interface IssueCardProps {
    issue: ValidationIssue;
}

export function IssueCard({ issue }: IssueCardProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    const hasSuggestion = issue.suggestion || issue.llmSuggestion;

    return (
        <div
            className={cn(
                'rounded-lg border border-white/10 bg-white/5 overflow-hidden transition-all duration-200',
                isExpanded && 'bg-white/10'
            )}
        >
            <button
                onClick={() => hasSuggestion && setIsExpanded(!isExpanded)}
                className={cn(
                    'w-full px-4 py-3 flex items-center justify-between text-left',
                    hasSuggestion && 'cursor-pointer hover:bg-white/5'
                )}
            >
                <div className="flex-1 min-w-0">
                    <p className="text-sm text-white">
                        {issue.description}
                    </p>
                    {issue.column && (
                        <span className="inline-flex items-center px-2 py-0.5 mt-1 rounded text-xs bg-white/10 text-gray-400">
                            📍 {issue.column}
                        </span>
                    )}
                </div>

                {hasSuggestion && (
                    <div className="flex items-center gap-2 ml-3">
                        <Lightbulb className="w-4 h-4 text-yellow-400" />
                        {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-gray-400" />
                        ) : (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                        )}
                    </div>
                )}
            </button>

            {/* Expanded content */}
            {isExpanded && hasSuggestion && (
                <div className="px-4 pb-3 pt-0 border-t border-white/10">
                    {issue.llmSuggestion ? (
                        <div className="mt-3 p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                            <p className="text-xs text-cyan-400 mb-1">🤖 AI Önerisi:</p>
                            <p className="text-sm text-gray-300">{issue.llmSuggestion}</p>
                        </div>
                    ) : (
                        <div className="mt-3 p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                            <p className="text-sm text-purple-300">
                                ✨ Detaylı AI önerileri almak için yukarıdaki butona tıklayın
                            </p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
