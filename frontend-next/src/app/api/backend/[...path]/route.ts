import { NextRequest, NextResponse } from 'next/server';

const BACKEND_BASE_URL = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

        const proxyResponse = new NextResponse(response.body, {
            status: response.status,
            headers: responseHeaders,
        });

        getSetCookieHeaders(response.headers).forEach((setCookie) => {
            proxyResponse.headers.append('Set-Cookie', setCookie);
        });

        return proxyResponse;
    } catch {
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
