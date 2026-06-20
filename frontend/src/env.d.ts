/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

declare module "mammoth" {
  export function convertToHtml(options: {
    arrayBuffer: ArrayBuffer;
  }): Promise<{ value: string; messages: any[] }>;
  export function extractRawText(options: {
    arrayBuffer: ArrayBuffer;
  }): Promise<{ value: string }>;
}
