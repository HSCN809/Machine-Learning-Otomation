import { Redis } from 'ioredis';
import { logger } from '@/lib/logger';

const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379/0';

let redisClient: Redis | null = null;
let redisInitializationAttempted = false;

function createRedisClient(): Redis {
    const client = new Redis(redisUrl, {
        lazyConnect: true,
        retryStrategy(times) {
            const delay = Math.min(times * 50, 2000);
            return delay;
        },
        maxRetriesPerRequest: 3,
    });

    client.on('connect', () => {
        logger.info('Connected to Redis');
    });

    client.on('error', (err) => {
        logger.error('Redis connection error', err);
    });

    return client;
}

export async function getRedisClient(): Promise<Redis | null> {
    if (redisClient) {
        return redisClient;
    }

    if (redisInitializationAttempted) {
        return null;
    }

    redisInitializationAttempted = true;

    try {
        const client = createRedisClient();
        await client.connect();
        redisClient = client;
        return redisClient;
    } catch (error) {
        logger.warn('Redis unavailable, continuing without proxy cache', {
            error: error instanceof Error ? error.message : String(error),
        });
        return null;
    }
}

export const CACHE_TTL = {
    DEFAULT: 60 * 5,
    LONG: 60 * 60,
    SHORT: 60,
};
