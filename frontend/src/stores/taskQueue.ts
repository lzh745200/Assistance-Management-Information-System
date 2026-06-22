import { defineStore } from 'pinia'
export const useTaskQueueStore = defineStore('taskQueue', {
  state: () => ({ tasks: [] as any[] }),
  actions: {
    add(task: any) {
      this.tasks.push(task)
    },
    remove(id: string) {
      this.tasks = this.tasks.filter((t) => t.id !== id)
    },
    clear() {
      this.tasks = []
    },
  },
})
