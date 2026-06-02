export interface FormField { key:string;label:string;type?:"text"|"number"|"select"|"date"|"textarea"|"switch";options?:{label:string;value:any}[];required?:boolean;placeholder?:string;default?:any }
export interface FormBuilderProps { fields:FormField[];model:Record<string,any>;labelWidth?:string }
