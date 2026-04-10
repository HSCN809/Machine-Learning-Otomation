'use client';

import { useEffect, useRef } from 'react';

interface TrailPoint {
    x: number;
    y: number;
    createdAt: number;
}

interface PixelTrailPointer {
    x: number;
    y: number;
}

interface PixelTrailProps {
    pointer: PixelTrailPointer | null;
    active: boolean;
    color?: string;
    gridSize?: number;
    trailSize?: number;
    maxAge?: number;
    interpolate?: number;
    className?: string;
}

export function PixelTrail({
    pointer,
    active,
    color = '#00D9FF',
    gridSize = 40,
    trailSize = 0.24,
    maxAge = 250,
    interpolate = 5,
    className,
}: PixelTrailProps) {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const pointsRef = useRef<TrailPoint[]>([]);
    const lastPointerRef = useRef<PixelTrailPointer | null>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const resizeCanvas = () => {
            const dpr = window.devicePixelRatio || 1;
            canvas.width = window.innerWidth * dpr;
            canvas.height = window.innerHeight * dpr;
            canvas.style.width = `${window.innerWidth}px`;
            canvas.style.height = `${window.innerHeight}px`;

            const context = canvas.getContext('2d');
            context?.setTransform(dpr, 0, 0, dpr, 0, 0);
        };

        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        return () => window.removeEventListener('resize', resizeCanvas);
    }, []);

    useEffect(() => {
        if (!pointer) {
            if (!active) {
                lastPointerRef.current = null;
            }
            return;
        }

        if (!active) {
            lastPointerRef.current = pointer;
            return;
        }

        const now = performance.now();
        const previousPointer = lastPointerRef.current;
        const nextPoints: TrailPoint[] = [];

        if (previousPointer) {
            const deltaX = pointer.x - previousPointer.x;
            const deltaY = pointer.y - previousPointer.y;
            const distance = Math.hypot(deltaX, deltaY);
            const steps = Math.max(1, Math.ceil(distance / Math.max(1, interpolate)));

            for (let step = 1; step <= steps; step += 1) {
                const progress = step / steps;
                nextPoints.push({
                    x: previousPointer.x + deltaX * progress,
                    y: previousPointer.y + deltaY * progress,
                    createdAt: now,
                });
            }
        } else {
            nextPoints.push({
                x: pointer.x,
                y: pointer.y,
                createdAt: now,
            });
        }

        pointsRef.current.push(...nextPoints);
        lastPointerRef.current = pointer;
    }, [active, interpolate, pointer]);

    useEffect(() => {
        const canvas = canvasRef.current;
        const context = canvas?.getContext('2d');
        if (!canvas || !context) return;

        let animationFrameId = 0;

        const hexToRgb = (hex: string) => {
            const normalized = hex.replace('#', '');
            const value =
                normalized.length === 3
                    ? normalized
                          .split('')
                          .map((char) => char + char)
                          .join('')
                    : normalized;

            const red = Number.parseInt(value.slice(0, 2), 16);
            const green = Number.parseInt(value.slice(2, 4), 16);
            const blue = Number.parseInt(value.slice(4, 6), 16);

            return { red, green, blue };
        };

        const { red, green, blue } = hexToRgb(color);
        const draw = () => {
            const now = performance.now();
            context.clearRect(0, 0, canvas.width, canvas.height);

            pointsRef.current = pointsRef.current.filter((point) => now - point.createdAt < maxAge);
            const pixelSize = Math.max(6, gridSize * trailSize);

            for (const point of pointsRef.current) {
                const age = now - point.createdAt;
                const alpha = 1 - age / maxAge;
                const snappedX = Math.round(point.x / gridSize) * gridSize;
                const snappedY = Math.round(point.y / gridSize) * gridSize;
                const size = pixelSize * (0.65 + alpha * 0.35);

                context.fillStyle = `rgba(${red}, ${green}, ${blue}, ${Math.max(0, alpha)})`;
                context.fillRect(snappedX - size / 2, snappedY - size / 2, size, size);
            }

            animationFrameId = window.requestAnimationFrame(draw);
        };

        animationFrameId = window.requestAnimationFrame(draw);
        return () => window.cancelAnimationFrame(animationFrameId);
    }, [color, gridSize, maxAge, trailSize]);

    return (
        <canvas
            ref={canvasRef}
            className={`pointer-events-none fixed inset-0 z-[45] ${className ?? ''}`}
            aria-hidden="true"
        />
    );
}
