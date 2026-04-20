import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const editorPath = resolve('src/components/data-upload/DataEditor.tsx');
const source = readFileSync(editorPath, 'utf8');

if (source.includes('Veri duzenleyici yukleniyor') || source.includes('Veri düzenleyici yükleniyor')) {
    throw new Error('DataEditor initial loading must use skeleton UI, not a text loading card.');
}

if (!source.includes('DataEditorSkeleton')) {
    throw new Error('DataEditor must render a dedicated initial skeleton.');
}

console.log('data editor loading skeleton assertion passed');
