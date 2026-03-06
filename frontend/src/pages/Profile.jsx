import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api';
import styles from './Profile.module.css';

const GENRES = ['fantasy', 'sci-fi', 'mystery', 'horror', 'adventure', 'comedy'];

export default function Profile({ profile, onUpdate }) {
  const [username, setUsername] = useState('');
  const [genre, setGenre] = useState('fantasy');
  const [saved, setSaved] = useState(false);

  const [gcalConnected, setGcalConnected] = useState(false);
  const [gcalLoading, setGcalLoading] = useState(true);
  const [syncResult, setSyncResult] = useState(null);
  const [gcalError, setGcalError] = useState(null);

  const [defaultKeywords, setDefaultKeywords] = useState({ hard: [], easy: [] });
  const [customHard, setCustomHard] = useState([]);
  const [customEasy, setCustomEasy] = useState([]);
  const [removedHard, setRemovedHard] = useState([]);
  const [removedEasy, setRemovedEasy] = useState([]);
  const [newHardKw, setNewHardKw] = useState('');
  const [newEasyKw, setNewEasyKw] = useState('');
  const [kwSaved, setKwSaved] = useState(false);

  const [searchParams, setSearchParams] = useSearchParams();

  const checkGcalStatus = useCallback(async () => {
    try {
      const status = await api.gcalStatus();
      setGcalConnected(status.connected);
    } catch {
      setGcalConnected(false);
    } finally {
      setGcalLoading(false);
    }
  }, []);

  const loadKeywords = useCallback(async () => {
    try {
      const data = await api.gcalGetKeywords();
      setDefaultKeywords(data.defaults);
      setCustomHard(data.custom.hard || []);
      setCustomEasy(data.custom.easy || []);
      setRemovedHard(data.custom.removed_hard || []);
      setRemovedEasy(data.custom.removed_easy || []);
    } catch { /* ignore if not connected */ }
  }, []);

  useEffect(() => {
    if (profile) {
      setUsername(profile.username);
      setGenre(profile.genre_preference);
    }
  }, [profile]);

  useEffect(() => {
    checkGcalStatus();
    loadKeywords();
  }, [checkGcalStatus, loadKeywords]);

  useEffect(() => {
    if (searchParams.get('gcal') === 'connected') {
      setGcalConnected(true);
      setSyncResult({ message: 'Google Calendar connected!' });
      searchParams.delete('gcal');
      setSearchParams(searchParams, { replace: true });
      setTimeout(() => setSyncResult(null), 4000);
    }
  }, [searchParams, setSearchParams]);

  const handleSave = async () => {
    await api.updateProfile({ username, genre_preference: genre });
    onUpdate();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleGcalConnect = async () => {
    try {
      setGcalError(null);
      const { url } = await api.gcalAuthUrl();
      window.location.href = url;
    } catch (err) {
      setGcalError(err.message);
    }
  };

  const handleGcalSync = async () => {
    try {
      setGcalError(null);
      setSyncResult(null);
      const result = await api.gcalSync();
      setSyncResult(result);
      setTimeout(() => setSyncResult(null), 5000);
    } catch (err) {
      setGcalError(err.message);
    }
  };

  const handleGcalDisconnect = async () => {
    try {
      setGcalError(null);
      await api.gcalDisconnect();
      setGcalConnected(false);
      setSyncResult(null);
    } catch (err) {
      setGcalError(err.message);
    }
  };

  const addKeyword = (type) => {
    const kw = (type === 'hard' ? newHardKw : newEasyKw).trim().toLowerCase();
    if (!kw) return;

    if (type === 'hard') {
      if (removedHard.includes(kw)) {
        setRemovedHard((prev) => prev.filter((k) => k !== kw));
      } else if (!defaultKeywords.hard.includes(kw) && !customHard.includes(kw)) {
        setCustomHard((prev) => [...prev, kw]);
      }
      setNewHardKw('');
    }
    if (type === 'easy') {
      if (removedEasy.includes(kw)) {
        setRemovedEasy((prev) => prev.filter((k) => k !== kw));
      } else if (!defaultKeywords.easy.includes(kw) && !customEasy.includes(kw)) {
        setCustomEasy((prev) => [...prev, kw]);
      }
      setNewEasyKw('');
    }
  };

  const removeDefaultKeyword = (type, kw) => {
    if (type === 'hard') setRemovedHard((prev) => [...prev, kw]);
    if (type === 'easy') setRemovedEasy((prev) => [...prev, kw]);
  };

  const removeCustomKeyword = (type, idx) => {
    if (type === 'hard') setCustomHard((prev) => prev.filter((_, i) => i !== idx));
    if (type === 'easy') setCustomEasy((prev) => prev.filter((_, i) => i !== idx));
  };

  const saveKeywords = async () => {
    try {
      await api.gcalUpdateKeywords({
        hard: customHard,
        easy: customEasy,
        removed_hard: removedHard,
        removed_easy: removedEasy,
      });
      setKwSaved(true);
      setTimeout(() => setKwSaved(false), 2000);
    } catch (err) {
      setGcalError(err.message);
    }
  };

  if (!profile) return <p>Loading...</p>;

  const xpForNext = 100 * profile.level;
  const xpPercent = Math.min(100, Math.round((profile.xp / xpForNext) * 100));

  return (
    <div>
      <h1>Adventurer Profile</h1>

      <div className={styles.statsGrid}>
        <div className={styles.stat}>
          <div className={styles.statLabel}>Level</div>
          <div className={styles.statValue}>{profile.level}</div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statLabel}>XP</div>
          <div className={styles.statValue}>{profile.xp} / {xpForNext}</div>
          <div className={styles.bar}>
            <div className={styles.barFill} style={{ width: `${xpPercent}%` }} />
          </div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statLabel}>Coins</div>
          <div className={styles.statValue}>{profile.coins}</div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statLabel}>Gems</div>
          <div className={styles.statValue}>{profile.gems}</div>
        </div>
      </div>

      <div className={styles.gcalSection}>
        <h2>Google Calendar</h2>
        {gcalLoading ? (
          <p className={styles.gcalMuted}>Checking connection...</p>
        ) : gcalConnected ? (
          <div className={styles.gcalConnected}>
            <span className={styles.gcalBadge}>Connected</span>
            <div className={styles.gcalActions}>
              <button className="btn-primary" onClick={handleGcalSync}>
                Sync Now
              </button>
              <button className={styles.gcalDisconnect} onClick={handleGcalDisconnect}>
                Disconnect
              </button>
            </div>
          </div>
        ) : (
          <button className="btn-primary" onClick={handleGcalConnect}>
            Connect Google Calendar
          </button>
        )}

        {syncResult && (
          <div className={styles.gcalResult}>
            {syncResult.message
              ? syncResult.message
              : `Imported ${syncResult.imported} event${syncResult.imported !== 1 ? 's' : ''}, skipped ${syncResult.skipped} duplicate${syncResult.skipped !== 1 ? 's' : ''}.`}
          </div>
        )}
        {gcalError && <div className={styles.gcalError}>{gcalError}</div>}

        <div className={styles.kwSection}>
          <h3>Difficulty Keywords</h3>
          <p className={styles.kwHint}>
            Events matching these words get auto-assigned a difficulty when synced.
          </p>

          <div className={styles.kwGroup}>
            <label className={styles.kwLabel}>Hard keywords</label>
            <div className={styles.kwTags}>
              {defaultKeywords.hard.filter((kw) => !removedHard.includes(kw)).map((kw) => (
                <span key={`dh-${kw}`} className={styles.kwTagDefault}>
                  {kw}
                  <button onClick={() => removeDefaultKeyword('hard', kw)}>&times;</button>
                </span>
              ))}
              {customHard.map((kw, i) => (
                <span key={`ch-${i}`} className={styles.kwTagCustom}>
                  {kw}
                  <button onClick={() => removeCustomKeyword('hard', i)}>&times;</button>
                </span>
              ))}
            </div>
            <div className={styles.kwAdd}>
              <input
                value={newHardKw}
                onChange={(e) => setNewHardKw(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addKeyword('hard')}
                placeholder="Add hard keyword..."
              />
              <button className="btn-primary" onClick={() => addKeyword('hard')}>+</button>
            </div>
          </div>

          <div className={styles.kwGroup}>
            <label className={styles.kwLabel}>Easy keywords</label>
            <div className={styles.kwTags}>
              {defaultKeywords.easy.filter((kw) => !removedEasy.includes(kw)).map((kw) => (
                <span key={`de-${kw}`} className={styles.kwTagDefault}>
                  {kw}
                  <button onClick={() => removeDefaultKeyword('easy', kw)}>&times;</button>
                </span>
              ))}
              {customEasy.map((kw, i) => (
                <span key={`ce-${i}`} className={styles.kwTagCustom}>
                  {kw}
                  <button onClick={() => removeCustomKeyword('easy', i)}>&times;</button>
                </span>
              ))}
            </div>
            <div className={styles.kwAdd}>
              <input
                value={newEasyKw}
                onChange={(e) => setNewEasyKw(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addKeyword('easy')}
                placeholder="Add easy keyword..."
              />
              <button className="btn-primary" onClick={() => addKeyword('easy')}>+</button>
            </div>
          </div>

          <div className={styles.kwFooter}>
            <button className="btn-primary" onClick={saveKeywords}>Save Keywords</button>
            {kwSaved && <span className={styles.saved}>Saved!</span>}
          </div>
        </div>
      </div>

      <div className={styles.form}>
        <label>Display Name</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} />

        <label>Story Genre Preference</label>
        <select value={genre} onChange={(e) => setGenre(e.target.value)}>
          {GENRES.map((g) => (
            <option key={g} value={g}>{g.charAt(0).toUpperCase() + g.slice(1)}</option>
          ))}
        </select>

        <button className="btn-primary" onClick={handleSave}>Save Profile</button>
        {saved && <span className={styles.saved}>Saved!</span>}
      </div>
    </div>
  );
}
