import type { EChartsOption } from "echarts";
export type ChartType = "line"|"bar"|"pie"|"area"|"scatter"|"radar"|"gauge";
export interface DataPoint { name:string;value:number|number[];[key:string]:any }
export interface SeriesData { name:string;data:(number|DataPoint)[];type?:ChartType;color?:string;smooth?:boolean;areaStyle?:Record<string,any>;[key:string]:any }
export interface ChartData { xAxis?:string[];yAxis?:string[];series:SeriesData[];legend?:string[] }
export interface ChartAction { icon:string;tooltip:string;onClick:()=>void;disabled?:boolean }
export interface ChartCardProps { title:string;subtitle?:string;type:ChartType;data:ChartData;options?:EChartsOption;loading?:boolean;height?:string|number;actions?:ChartAction[];showLegend?:boolean;showToolbox?:boolean;theme?:"light"|"dark"|"military";autoResize?:boolean;emptyText?:string }
export interface ChartCardEmits { (e:"chart-click",params:any):void;(e:"legend-select-changed",params:{name:string;selected:Record<string,boolean>}):void;(e:"data-zoom",params:{start:number;end:number}):void;(e:"rendered"):void }
export interface ChartCardExpose { getChartInstance:()=>any;refresh:()=>void;resize:()=>void;exportImage:(type?:"png"|"jpeg")=>string;setOption:(option:EChartsOption,notMerge?:boolean)=>void;showLoading:()=>void;hideLoading:()=>void }
