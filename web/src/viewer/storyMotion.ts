import { chapterIds } from "./choreography";
/** Imperative scroll channel: camera updates never rerender the React page. */
export function createStoryMotion() {
  let progress = 0;
  let following = true;
  const pointer = { x: 0, y: 0 };
  const listeners = new Set<() => void>();
  const notify = () => listeners.forEach((listener) => listener());
  return {
    pointer,
    get progress() {
      return progress;
    },
    get following() {
      return following;
    },
    setProgress(value: number) {
      progress = Math.max(0, Math.min(chapterIds.length - 1, value));
      notify();
    },
    follow(value: boolean) {
      following = value;
      notify();
    },
    move(x: number, y: number) {
      pointer.x = x;
      pointer.y = y;
      notify();
    },
    subscribe(listener: () => void) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
  };
}
export type StoryMotion = ReturnType<typeof createStoryMotion>;
