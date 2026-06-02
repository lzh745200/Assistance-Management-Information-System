/// <reference types="vite/client" />

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

declare module "@antv/g6" {
  const G6: any;
  export default G6;
  export const Graph: any;
  export const TreeGraph: any;
  export const registerNode: any;
  export const registerEdge: any;
}

declare module "mammoth" {
  export function convertToHtml(options: {
    arrayBuffer: ArrayBuffer;
  }): Promise<{ value: string; messages: any[] }>;
  export function extractRawText(options: {
    arrayBuffer: ArrayBuffer;
  }): Promise<{ value: string }>;
}
