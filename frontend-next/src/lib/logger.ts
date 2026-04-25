type LogContext = Record<string, unknown>;

const isDevelopment = process.env.NODE_ENV !== 'production';

function normalizeError(error: unknown): LogContext {
    if (error instanceof Error) {
        return {
            name: error.name,
            message: error.message,
            stack: error.stack,
        };
    }

    return { error };
}

function writeLog(
    level: 'debug' | 'info' | 'warn' | 'error',
    message: string,
    context?: LogContext
): void {
    if (!isDevelopment && level !== 'error') {
        return;
    }

    const payload = context ? ['[ML Automation]', message, context] : ['[ML Automation]', message];
    console[level](...payload);
}

export const logger = {
    debug(message: string, context?: LogContext): void {
        writeLog('debug', message, context);
    },
    info(message: string, context?: LogContext): void {
        writeLog('info', message, context);
    },
    warn(message: string, context?: LogContext): void {
        writeLog('warn', message, context);
    },
    error(message: string, error?: unknown, context?: LogContext): void {
        writeLog('error', message, {
            ...(error === undefined ? {} : normalizeError(error)),
            ...context,
        });
    },
};
