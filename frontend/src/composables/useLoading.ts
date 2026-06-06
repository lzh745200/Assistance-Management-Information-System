export function useLoading() {
  const isLoading = ref(false);
  const start = () => {
    isLoading.value = true;
  };
  const stop = () => {
    isLoading.value = false;
  };
  return { isLoading, start, stop };
}
