import { toast } from 'sonner';

export function getErrorMessage(error: unknown, fallback: string): string {
    return error instanceof Error && error.message ? error.message : fallback;
}

export const notify = {
    success(message: string): void {
        toast.success(message);
    },
    info(message: string): void {
        toast.info(message);
    },
    warning(message: string): void {
        toast.warning(message);
    },
    error(error: unknown, fallback: string): void {
        toast.error(getErrorMessage(error, fallback));
    },
    loading(message: string): string | number {
        return toast.loading(message);
    },
    dismiss(id?: string | number): void {
        toast.dismiss(id);
    },
};
