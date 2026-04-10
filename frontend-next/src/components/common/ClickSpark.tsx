'use client';

import { useCallback, useEffect, useRef } from 'react';

type ClickSparkEasing = 'linear' | 'ease-in' | 'ease-out' | 'ease-in-out';

interface Spark {
    x: number;
    y: number;
    angle: number;
    startTime: number;
}

interface ClickSparkProps {
    children: React.ReactNode;
    className?: string;
    sparkColor?: string;
    sparkSize?: number;
    sparkRadius?: number;
    sparkCount?: number;
    duration?: number;
    easing?: ClickSparkEasing;
    extraScale?: number;
    disabled?: boolean;
}

export function ClickSpark({
    children,
    className,
    sparkColor = '#ffffff',
    sparkSize = 10,
    sparkRadius = 15,
    sparkCount = 8,
    duration = 400,
    easing = 'ease-out',
    extraScale = 1,
    disabled = false,
}: ClickSparkProps) {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const sparksRef = useRef<Spark[]>([]);

    useEffect(() => {
        const canvas = canvasRef.current;
        const parent = canvas?.parentElement;
        if (!canvas || !parent) return;

        const resizeCanvas = () => {
            const rect = parent.getBoundingClientRect();
            const dpr = window.devicePixelRatio || 1;
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            canvas.style.width = `${rect.width}px`;
            canvas.style.height = `${rect.height}px`;

            const context = canvas.getContext('2d');
            context?.setTransform(dpr, 0, 0, dpr, 0, 0);
        };

        resizeCanvas();
        const observer = new ResizeObserver(resizeCanvas);
        observer.observe(parent);

        return () => observer.disconnect();
    }, []);

    const ease = useCallback(
        (value: number) => {
            switch (easing) {
                case 'linear':
                    return value;
                case 'ease-in':
                    return value * value;
                case 'ease-in-out':
                    return value < 0.5 ? 2 * value * value : -1 + (4 - 2 * value) * value;
                case 'ease-out':
                default:
                    return value * (2 - value);
            }
        },
        [easing]
    );

    useEffect(() => {
        const canvas = canvasRef.current;
        const context = canvas?.getContext('2d');
        if (!canvas || !context) return;

        let animationFrameId = 0;

        const draw = (timestamp: number) => {
            context.clearRect(0, 0, canvas.width, canvas.height);

            sparksRef.current = sparksRef.current.filter((spark) => {
                const elapsed = timestamp - spark.startTime;
                if (elapsed >= duration) {
                    return false;
                }

                const progress = elapsed / duration;
                const eased = ease(progress);
                const distance = eased * sparkRadius * extraScale;
                const lineLength = sparkSize * (1 - eased);
                const opacity = 1 - progress;
                const startX = spark.x + distance * Math.cos(spark.angle);
                const startY = spark.y + distance * Math.sin(spark.angle);
                const endX = spark.x + (distance + lineLength) * Math.cos(spark.angle);
                const endY = spark.y + (distance + lineLength) * Math.sin(spark.angle);

                context.strokeStyle = sparkColor;
                context.globalAlpha = opacity;
                context.lineWidth = 2;
                context.beginPath();
                context.moveTo(startX, startY);
                context.lineTo(endX, endY);
                context.stroke();
                context.globalAlpha = 1;

                return true;
            });

            animationFrameId = window.requestAnimationFrame(draw);
        };

        animationFrameId = window.requestAnimationFrame(draw);
        return () => window.cancelAnimationFrame(animationFrameId);
    }, [duration, ease, extraScale, sparkColor, sparkRadius, sparkSize]);

    const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
        if (disabled || event.button !== 0) return;

        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const now = performance.now();

        const nextSparks = Array.from({ length: sparkCount }, (_, index) => ({
            x,
            y,
            angle: (2 * Math.PI * index) / sparkCount,
            startTime: now,
        }));

        sparksRef.current.push(...nextSparks);
    };

    return (
        <div className={className} onClick={handleClick} style={{ position: 'relative' }}>
            <canvas
                ref={canvasRef}
                className="pointer-events-none absolute inset-0 block h-full w-full select-none"
            />
            {children}
        </div>
    );
}
