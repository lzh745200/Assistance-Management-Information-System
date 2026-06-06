export function useMenuPermission() {
  const hasPermission = (_menuKey: string) => true;
  return { hasPermission };
}
