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

    return (
        <div
            className={cn(
                'rounded-lg border border-white/10 bg-white/5 overflow-hidden transition-all duration-200',
                isExpanded && 'bg-white/10'
            )}
        >
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between text-left cursor-pointer hover:bg-white/5"
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

                <div className="flex items-center gap-2 ml-3">
                    <Lightbulb className="w-4 h-4 text-gray-500" />
                    {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-gray-400" />
                    ) : (
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                    )}
                </div>
            </button>

            {isExpanded && issue.suggestion && (
                <div className="px-4 pb-3 pt-0 border-t border-white/10">
                    <div className="mt-3 p-3 rounded-lg bg-white/5 border border-white/10">
                        <p className="text-xs text-gray-400 mb-1">Öneri:</p>
                        <p className="text-sm text-gray-300">{issue.suggestion}</p>
                    </div>
                </div>
            )}
        </div>
    );
}