import { useEffect, useRef, useState, useCallback } from 'react';
import { api } from '../api';
import { subscribe, setNarrationEntry, getNarrationState } from '../narrationStore';
import styles from './Story.module.css';

export default function Story() {
  const [segments, setSegments] = useState([]);
  const [archives, setArchives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [showModal, setShowModal] = useState(false);
  const [chapterName, setChapterName] = useState('');
  const [archiving, setArchiving] = useState(false);

  const [expanded, setExpanded] = useState({});
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');

  // narration state is kept in the module-level store so fetches survive tab switches
  const [narration, setNarration] = useState(getNarrationState);

  // rating UI per segment: { [segId]: { feedbackOpen: bool, feedbackText: string } }
  const [ratingUI, setRatingUI] = useState({});

  const modalInputRef = useRef(null);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const [segs, archs] = await Promise.all([api.getStory(), api.getArchives()]);
      setSegments(segs);
      setArchives(archs);
    } catch {
      setError('Failed to load story.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  // Sync with the module-level narration store (survives tab switching)
  useEffect(() => subscribe(setNarration), []);

  const handleNarrate = useCallback(async (archiveId) => {
    if (getNarrationState()[archiveId]?.url) return; // already generated
    setNarrationEntry(archiveId, { loading: true, url: null, error: null });
    try {
      const blob = await api.narrateArchive(archiveId);
      const url = URL.createObjectURL(blob);
      setNarrationEntry(archiveId, { loading: false, url, error: null });
    } catch (e) {
      setNarrationEntry(archiveId, { loading: false, url: null, error: e.message });
    }
  }, []);

  const openModal = () => {
    setChapterName(`Chapter ${archives.length + 1}`);
    setShowModal(true);
    setTimeout(() => modalInputRef.current?.select(), 50);
  };

  const handleArchive = async () => {
    if (!chapterName.trim()) return;
    try {
      setArchiving(true);
      await api.archiveStory(chapterName.trim());
      setShowModal(false);
      await load();
    } catch {
      setError('Failed to save chapter.');
      setArchiving(false);
    }
  };

  const handleRate = async (segId, newRating, currentRating, feedback) => {
    // Toggle off if same rating clicked again
    const finalRating = newRating === currentRating ? 0 : newRating;
    try {
      await api.rateSegment(segId, finalRating, feedback || null);
      setSegments((prev) =>
        prev.map((s) => s.id === segId ? { ...s, rating: finalRating, feedback: feedback || null } : s)
      );
      setRatingUI((prev) => ({ ...prev, [segId]: { feedbackOpen: false, feedbackText: '' } }));
    } catch {
      // silently fail — rating is non-critical
    }
  };

  const openFeedback = (segId) =>
    setRatingUI((prev) => ({ ...prev, [segId]: { feedbackOpen: true, feedbackText: prev[segId]?.feedbackText || '' } }));

  const closeFeedback = (segId) =>
    setRatingUI((prev) => ({ ...prev, [segId]: { ...prev[segId], feedbackOpen: false } }));

  const toggleExpanded = (id) =>
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));

  const startRename = (archive, e) => {
    e.stopPropagation();
    setRenamingId(archive.id);
    setRenameValue(archive.title);
  };

  const commitRename = async (id, e) => {
    e?.stopPropagation();
    if (!renameValue.trim()) { setRenamingId(null); return; }
    try {
      await api.renameArchive(id, renameValue.trim());
      setArchives((prev) => prev.map((a) => a.id === id ? { ...a, title: renameValue.trim() } : a));
    } catch {
      setError('Failed to rename chapter.');
    } finally {
      setRenamingId(null);
    }
  };

  const handleDeleteArchive = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this archived chapter permanently?')) return;
    try {
      await api.deleteArchive(id);
      setArchives((prev) => prev.filter((a) => a.id !== id));
    } catch {
      setError('Failed to delete chapter.');
    }
  };

  return (
    <div className={styles.page}>

      {/* ── Save-chapter modal ────────────────────────── */}
      {showModal && (
        <div className={styles.modalOverlay} onClick={() => setShowModal(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>Save This Chapter</h2>
            <p className={styles.modalSub}>Give this chapter a name before beginning a new tale.</p>
            <input
              ref={modalInputRef}
              className={styles.modalInput}
              value={chapterName}
              onChange={(e) => setChapterName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleArchive()}
              placeholder="Chapter name..."
            />
            <div className={styles.modalActions}>
              <button
                className="btn-primary"
                onClick={handleArchive}
                disabled={archiving || !chapterName.trim()}
              >
                {archiving ? 'Saving...' : 'Save & Begin New Tale'}
              </button>
              <button className={styles.modalCancel} onClick={() => setShowModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Header ───────────────────────────────────── */}
      <div className={styles.header}>
        <div className={styles.titleGroup}>
          <h1>Chronicle of Adventures</h1>
          <div className={styles.subtitle}>Follow the tale woven from your completed quests.</div>
        </div>
        <button
          className="btn-secondary"
          onClick={openModal}
          disabled={segments.length === 0}
        >
          New Story
        </button>
      </div>

      {/* ── Active story scroll ───────────────────────── */}
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
          {!loading && !error && segments.map((seg, index) => {
            const ui = ratingUI[seg.id] || {};
            return (
              <div
                key={seg.id}
                className={styles.segment}
                style={{ animationDelay: `${index * 60}ms` }}
              >
                {seg.task_title && (
                  <div className={styles.questSource}>
                    <span className={styles.questIcon}>⚔</span> {seg.task_title}
                  </div>
                )}
                <div className={styles.chapterLabel}>Chapter {index + 1}</div>
                <div className={styles.segmentMeta}>
                  {seg.genre} · {new Date(seg.created_at).toLocaleString()}
                </div>
                <div className={styles.segmentText}>{seg.content}</div>
                <div className={styles.ratingRow}>
                  <button
                    className={`${styles.ratingBtn} ${seg.rating === 1 ? styles.ratingBtnLike : ''}`}
                    title="I liked this"
                    onClick={() => {
                      if (seg.rating === 1) { handleRate(seg.id, 1, 1, null); }
                      else { openFeedback(seg.id); setRatingUI((prev) => ({ ...prev, [seg.id]: { ...prev[seg.id], pendingRating: 1, feedbackOpen: true, feedbackText: prev[seg.id]?.feedbackText || '' } })); }
                    }}
                  >👍</button>
                  <button
                    className={`${styles.ratingBtn} ${seg.rating === -1 ? styles.ratingBtnDislike : ''}`}
                    title="I disliked this"
                    onClick={() => {
                      if (seg.rating === -1) { handleRate(seg.id, -1, -1, null); }
                      else { setRatingUI((prev) => ({ ...prev, [seg.id]: { ...prev[seg.id], pendingRating: -1, feedbackOpen: true, feedbackText: prev[seg.id]?.feedbackText || '' } })); }
                    }}
                  >👎</button>
                  {seg.feedback && !ui.feedbackOpen && (
                    <span className={styles.ratingFeedbackHint}>{seg.feedback}</span>
                  )}
                </div>
                {ui.feedbackOpen && (
                  <div className={styles.feedbackBox}>
                    <textarea
                      className={styles.feedbackTextarea}
                      placeholder={ui.pendingRating === 1 ? "What did you enjoy? (optional)" : "What didn't you like? (optional)"}
                      value={ui.feedbackText || ''}
                      onChange={(e) => setRatingUI((prev) => ({ ...prev, [seg.id]: { ...prev[seg.id], feedbackText: e.target.value } }))}
                      rows={2}
                      autoFocus
                    />
                    <div className={styles.feedbackActions}>
                      <button
                        className={styles.feedbackSave}
                        onClick={() => handleRate(seg.id, ui.pendingRating, seg.rating, ui.feedbackText)}
                      >Save</button>
                      <button
                        className={styles.feedbackSkip}
                        onClick={() => handleRate(seg.id, ui.pendingRating, seg.rating, null)}
                      >Just rate, no note</button>
                      <button className={styles.feedbackCancel} onClick={() => closeFeedback(seg.id)}>Cancel</button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Archived chapters ─────────────────────────── */}
      {archives.length > 0 && (
        <div className={styles.archivesSection}>
          <h2 className={styles.archivesHeading}>Past Chronicles</h2>
          {archives.map((archive) => (
            <div key={archive.id} className={styles.archiveCard}>
              {/* Narration row */}
              <div className={styles.narrateRow}>
                {narration[archive.id]?.url ? (
                  <audio
                    key={narration[archive.id].url}
                    controls
                    autoPlay
                    src={narration[archive.id].url}
                    className={styles.audioPlayer}
                  />
                ) : (
                  <button
                    className={styles.narrateBtn}
                    onClick={() => handleNarrate(archive.id)}
                    disabled={narration[archive.id]?.loading}
                  >
                    {narration[archive.id]?.loading
                      ? <><span className={styles.narrateSpinner} />Summoning Quinton Questly...</>
                      : <>🎙 Hear Quinton Questly narrate!</>}
                  </button>
                )}
                {narration[archive.id]?.error && (
                  <span className={styles.narrateError}>{narration[archive.id].error}</span>
                )}
              </div>

              <div
                className={styles.archiveHeader}
                onClick={() => toggleExpanded(archive.id)}
              >
                <div className={styles.archiveTitleRow}>
                  {renamingId === archive.id ? (
                    <>
                      <input
                        className={styles.renameInput}
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') commitRename(archive.id, e);
                          if (e.key === 'Escape') setRenamingId(null);
                        }}
                        onClick={(e) => e.stopPropagation()}
                        autoFocus
                      />
                      <button
                        className={styles.renameConfirm}
                        onClick={(e) => commitRename(archive.id, e)}
                        title="Confirm"
                      >✓</button>
                    </>
                  ) : (
                    <>
                      <span className={styles.archiveName}>{archive.title}</span>
                      <button
                        className={styles.renameBtn}
                        onClick={(e) => startRename(archive, e)}
                        title="Rename chapter"
                      >✎</button>
                      <button
                        className={styles.deleteArchiveBtn}
                        onClick={(e) => handleDeleteArchive(archive.id, e)}
                        title="Delete chapter"
                      >✕</button>
                    </>
                  )}
                </div>
                <div className={styles.archiveMeta}>
                  {archive.segments.length} segment{archive.segments.length !== 1 ? 's' : ''} ·{' '}
                  {new Date(archive.created_at).toLocaleDateString()}
                </div>
                <span className={styles.toggleIcon}>
                  {expanded[archive.id] ? '▲' : '▼'}
                </span>
              </div>

              {expanded[archive.id] && (
                <div className={styles.archiveContent}>
                  {archive.segments.map((seg, i) => (
                    <div key={i} className={styles.archiveSegment}>
                      {seg.task_title && (
                        <div className={styles.questSource}>
                          <span className={styles.questIcon}>⚔</span> {seg.task_title}
                        </div>
                      )}
                      <div className={styles.chapterLabel}>Chapter {i + 1}</div>
                      <div className={styles.segmentMeta}>
                        {seg.genre} · {new Date(seg.created_at).toLocaleString()}
                      </div>
                      <div className={styles.segmentText}>{seg.content}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
