import { Redis } from 'ioredis';
import { logger } from '@/lib/logger';

const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379/0';

class RedisClient {
    private static instance: Redis;

    public static getInstance(): Redis {
        if (!RedisClient.instance) {
            RedisClient.instance = new Redis(redisUrl, {
                retryStrategy(times) {
                    const delay = Math.min(times * 50, 2000);
                    return delay;
                },
                maxRetriesPerRequest: 3,
            });

            RedisClient.instance.on('connect', () => {
                logger.info('Connected to Redis');
            });

            RedisClient.instance.on('error', (err) => {
                logger.error('Redis connection error', err);
            });
        }

        return RedisClient.instance;
    }
}

export const redisClient = RedisClient.getInstance();

export const CACHE_TTL = {
    DEFAULT: 60 * 5, // 5 minutes
    LONG: 60 * 60, // 1 hour
    SHORT: 60, // 1 minute
};
