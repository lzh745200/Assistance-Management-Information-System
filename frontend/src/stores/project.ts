import { defineStore } from "pinia";

interface ProjectState {
  projects: any[];
  currentProject: any;
}

export const useProjectStore = defineStore("project", {
  state: (): ProjectState => ({ projects: [], currentProject: null }),
  actions: {
    setProjects(list: any[]) {
      this.projects = list;
    },
    setCurrent(p: any) {
      this.currentProject = p;
    },
  },
});
