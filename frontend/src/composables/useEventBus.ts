/**
 * 事件总线 Composable
 */
type EventHandler = (...args: any[]) => void;

const eventHandlers = new Map<string, Set<EventHandler>>();

export function getEventBus() {
  function on(event: string, handler: EventHandler) {
    if (!eventHandlers.has(event)) {
      eventHandlers.set(event, new Set());
    }
    eventHandlers.get(event)!.add(handler);
  }

  function off(event: string, handler: EventHandler) {
    eventHandlers.get(event)?.delete(handler);
  }

  function emit(event: string, ...args: any[]) {
    eventHandlers.get(event)?.forEach((handler) => handler(...args));
  }

  return { on, off, emit };
}

export function useEventBus() {
  return getEventBus();
}
