import { useEffect, useState } from 'react';
import { api } from '../api';
import styles from './Story.module.css';

export default function Story() {
  const [segments, setSegments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [error, setError] = useState(null);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getStory();
      setSegments(data);
    } catch (e) {
      console.error(e);
      setError('Failed to load story.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleReset = async () => {
    if (!window.confirm('Start a brand new tale? This will clear all previous story segments.')) return;
    try {
      setResetting(true);
      await api.resetStory();
      await load();
    } catch (e) {
      console.error(e);
      setError('Failed to reset story.');
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div className={styles.titleGroup}>
          <h1>Chronicle of Adventures</h1>
          <div className={styles.subtitle}>
            Follow the tale woven from your completed quests.
          </div>
        </div>
        <div>
          <button
            className="btn-secondary"
            onClick={handleReset}
            disabled={resetting || segments.length === 0}
          >
            {resetting ? 'Resetting...' : 'New Story'}
          </button>
          {segments.length > 0 && (
            <div className={styles.resetHint}>
              Clears all segments; the next completed quest will start a fresh tale.
            </div>
          )}
        </div>
      </div>

      <div className={styles.scroll}>
        <div className={styles.parchmentEdge} />
        <div className={styles.content}>
          {loading && <p className={styles.empty}>Summoning your tale...</p>}
          {error && <p className={styles.empty}>{error}</p>}
          {!loading && !error && segments.length === 0 && (
            <p className={styles.empty}>
              Your chronicle is blank. Complete a quest to write the opening lines.
            </p>
          )}
          {!loading && !error && segments.map((seg, index) => (
            <div
              key={seg.id}
              className={styles.segment}
              style={{ animationDelay: `${index * 60}ms` }}
            >
              <div className={styles.chapterLabel}>
                Chapter {index + 1}
              </div>
              <div className={styles.segmentMeta}>
                {seg.genre} • {new Date(seg.created_at).toLocaleString()}
              </div>
              <div className={styles.segmentText}>
                {seg.content}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

