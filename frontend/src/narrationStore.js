/**
 * Module-level narration store.
 * Lives outside React so fetch results survive component unmounts (tab switching).
 * archiveId -> { loading: bool, url: string|null, error: string|null }
 */
const _state = {};
const _listeners = new Set();

export function subscribe(fn) {
  _listeners.add(fn);
  fn({ ..._state });
  return () => _listeners.delete(fn);
}

export function setNarrationEntry(archiveId, entry) {
  _state[archiveId] = entry;
  _listeners.forEach((fn) => fn({ ..._state }));
}

export function getNarrationState() {
  return { ..._state };
}
