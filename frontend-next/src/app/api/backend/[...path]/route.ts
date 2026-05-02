import { NextRequest, NextResponse } from 'next/server';
import { logger } from '@/lib/logger';
import { CACHE_TTL, getRedisClient } from '@/lib/redis';

const BACKEND_BASE_URL =
    process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

type HeadersWithSetCookie = Headers & {
    getSetCookie?: () => string[];
};

function getSetCookieHeaders(headers: Headers): string[] {
    const setCookies = (headers as HeadersWithSetCookie).getSetCookie?.();
    if (setCookies && setCookies.length > 0) {
        return setCookies;
    }

    const setCookie = headers.get('set-cookie');
    return setCookie ? [setCookie] : [];
}

async function forward(request: NextRequest, params: { path: string[] }) {
    const targetPath = params.path.join('/');
    const targetUrl = new URL(`/${targetPath}`, BACKEND_BASE_URL);
    request.nextUrl.searchParams.forEach((value, key) => {
        targetUrl.searchParams.set(key, value);
    });

    const headers = new Headers();
    request.headers.forEach((value, key) => {
        if (key.toLowerCase() === 'host') {
            return;
        }
        headers.set(key, value);
    });

    const init: RequestInit = {
        method: request.method,
        headers,
        redirect: 'manual',
        cache: 'no-store',
    };

    const isGet = request.method === 'GET';
    const hasSessionHeader = Boolean(headers.get('x-session-id'));
    const hasAuthCookie = Boolean(headers.get('cookie'));
    const isAuthRoute = targetPath.startsWith('api/auth');
    const shouldUseProxyCache = isGet && !hasSessionHeader && !hasAuthCookie && !isAuthRoute;
    const cacheKey = shouldUseProxyCache ? `proxy_cache:${targetUrl.toString()}` : null;
    const redisClient = cacheKey ? await getRedisClient() : null;

    if (cacheKey && redisClient) {
        try {
            const cachedData = await redisClient.get(cacheKey);
            if (cachedData) {
                logger.info(`Cache hit for ${targetUrl.toString()}`);
                const { status, headers: cachedHeaders, body } = JSON.parse(cachedData);

                const responseHeaders = new Headers(cachedHeaders);
                responseHeaders.set('X-Cache', 'HIT');

                return new NextResponse(body, {
                    status,
                    headers: responseHeaders,
                });
            }
        } catch (error) {
            logger.error('Redis cache read error', error);
        }
    }

    if (request.method !== 'GET' && request.method !== 'HEAD') {
        init.body = await request.arrayBuffer();
    }

    try {
        const response = await fetch(targetUrl, init);
        const responseHeaders = new Headers();
        response.headers.forEach((value, key) => {
            const normalizedKey = key.toLowerCase();
            if (normalizedKey === 'content-length' || normalizedKey === 'set-cookie') {
                return;
            }
            responseHeaders.set(key, value);
        });

        const responseBody = await response.text();

        const proxyResponse = new NextResponse(responseBody, {
            status: response.status,
            headers: responseHeaders,
        });

        getSetCookieHeaders(response.headers).forEach((setCookie) => {
            proxyResponse.headers.append('Set-Cookie', setCookie);
        });

        if (cacheKey && response.ok && redisClient) {
            try {
                const cacheData = JSON.stringify({
                    status: response.status,
                    headers: Array.from(responseHeaders.entries()),
                    body: responseBody,
                });
                await redisClient.setex(cacheKey, CACHE_TTL.SHORT, cacheData);
                proxyResponse.headers.set('X-Cache', 'MISS');
            } catch (error) {
                logger.error('Redis cache write error', error);
            }
        }

        return proxyResponse;
    } catch (error) {
        logger.error('Backend proxy request failed', error, {
            method: request.method,
            targetUrl: targetUrl.toString(),
        });
        return NextResponse.json(
            {
                detail: 'Backend service unavailable. Start FastAPI server and verify PostgreSQL connection.',
            },
            { status: 503 }
        );
    }
}

export async function GET(
    request: NextRequest,
    context: { params: Promise<{ path: string[] }> }
) {
    return forward(request, await context.params);
}

export async function POST(
    request: NextRequest,
    context: { params: Promise<{ path: string[] }> }
) {
    return forward(request, await context.params);
}

export async function PUT(
    request: NextRequest,
    context: { params: Promise<{ path: string[] }> }
) {
    return forward(request, await context.params);
}

export async function PATCH(
    request: NextRequest,
    context: { params: Promise<{ path: string[] }> }
) {
    return forward(request, await context.params);
}

export async function DELETE(
    request: NextRequest,
    context: { params: Promise<{ path: string[] }> }
) {
    return forward(request, await context.params);
}

export async function OPTIONS(
    request: NextRequest,
    context: { params: Promise<{ path: string[] }> }
) {
    return forward(request, await context.params);
}
