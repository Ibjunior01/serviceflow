export function formatOrderNumber(n: number): string {
    return `OS-${String(n).padStart(4, '0')}`;
}