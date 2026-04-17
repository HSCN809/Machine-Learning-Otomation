import { redirect } from 'next/navigation';

import { HOMEPAGE_PATH } from '@/lib/routing';

export default function RootPage() {
    redirect(HOMEPAGE_PATH);
}
