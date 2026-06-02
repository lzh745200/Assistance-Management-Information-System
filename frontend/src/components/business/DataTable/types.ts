export interface Column { key:string;label:string;width?:number;sortable?:boolean;formatter?:(v:any)=>string }
export interface DataTableProps { data:any[];columns:Column[];loading?:boolean;pagination?:boolean;total?:number;pageSize?:number }
export interface DataTableEmits { (e:"page-change",page:number):void;(e:"sort-change",params:{prop:string;order:string}):void;(e:"selection-change",rows:any[]):void }
