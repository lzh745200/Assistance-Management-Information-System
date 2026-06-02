/**
 * 资源预加载 Composable
 */
import { ref } from "vue";

export function useResourcePreloader() {
  const loaded = ref(false);
  const progress = ref(0);

  async function preloadImages(urls: string[]) {
    let count = 0;
    const promises = urls.map(
      (url) =>
        new Promise<void>((resolve) => {
          const img = new Image();
          img.onload = img.onerror = () => {
            count++;
            progress.value = Math.round((count / urls.length) * 100);
            resolve();
          };
          img.src = url;
        }),
    );
    await Promise.all(promises);
    loaded.value = true;
  }

  return { loaded, progress, preloadImages };
}
