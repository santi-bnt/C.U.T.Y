/** Imperative scroll channel: camera updates never rerender the React page. */
export function createStoryMotion() {
  let progress = 0;
  let following = true;
  const listeners = new Set<() => void>();
  const notify = () => listeners.forEach((listener) => listener());
  return {
    get progress() {
      return progress;
    },
    get following() {
      return following;
    },
    setProgress(value: number) {
      progress = Math.max(0, Math.min(1, value));
      notify();
    },
    follow(value: boolean) {
      following = value;
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
