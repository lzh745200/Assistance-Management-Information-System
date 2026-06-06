import { defineStore } from "pinia";
export const useProjectStore = defineStore("project", {
  state: () => ({ projects: [], currentProject: null }),
  actions: {
    setProjects(list: any[]) {
      this.projects = list;
    },
    setCurrent(p: any) {
      this.currentProject = p;
    },
  },
});
