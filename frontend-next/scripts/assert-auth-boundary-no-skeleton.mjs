import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const boundaryPath = resolve('src/components/auth/ProtectedRouteBoundary.tsx');
const source = readFileSync(boundaryPath, 'utf8');

if (source.includes("guardState === 'bootstrap'") || source.includes('h-[420px]')) {
    throw new Error('ProtectedRouteBoundary must not render a shared bootstrap skeleton.');
}

console.log('auth boundary skeleton assertion passed');
