import { defineStore } from "pinia";
import { ref } from "vue";

export const useRouteStore = defineStore("route", () => {
  const routes = ref<any[]>([]);
  const addRoutes = ref<any[]>([]);

  function setRoutes(r: any[]) {
    routes.value = r;
  }

  function setAddRoutes(r: any[]) {
    addRoutes.value = r;
  }

  return { routes, addRoutes, setRoutes, setAddRoutes };
});