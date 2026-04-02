import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api';
import styles from './Profile.module.css';

const GENRES = ['fantasy', 'sci-fi', 'mystery', 'horror', 'adventure', 'comedy'];
const CHAR_ROLES = ['ally', 'rival', 'mentor', 'companion', 'antagonist', 'wildcard'];
const SLOTS = ['hat', 'face', 'body', 'hand'];
const SLOT_LABELS = { hat: 'Hat', face: 'Face', body: 'Body', hand: 'Hand' };
const LAYER_ORDER = ['body', 'hand', 'face', 'hat'];

export default function Profile({ profile, onUpdate }) {
  const [username, setUsername] = useState('');
  const [genre, setGenre] = useState('fantasy');
  const [saved, setSaved] = useState(false);
  const [shopItems, setShopItems] = useState([]);

  const [showSettings, setShowSettings] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [devUsed, setDevUsed] = useState(false);

  const [gcalConnected, setGcalConnected] = useState(false);
  const [gcalLoading, setGcalLoading] = useState(true);
  const [syncResult, setSyncResult] = useState(null);
  const [gcalError, setGcalError] = useState(null);

  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailLoading, setGmailLoading] = useState(true);
  const [gmailSyncResult, setGmailSyncResult] = useState(null);
  const [gmailError, setGmailError] = useState(null);
  const [gmailSyncing, setGmailSyncing] = useState(false);

  const [defaultKeywords, setDefaultKeywords] = useState({ hard: [], easy: [] });
  const [customHard, setCustomHard] = useState([]);
  const [customEasy, setCustomEasy] = useState([]);
  const [removedHard, setRemovedHard] = useState([]);
  const [removedEasy, setRemovedEasy] = useState([]);
  const [newHardKw, setNewHardKw] = useState('');
  const [newEasyKw, setNewEasyKw] = useState('');
  const [kwSaved, setKwSaved] = useState(false);

  const [userLikes, setUserLikes] = useState([]);
  const [userDislikes, setUserDislikes] = useState([]);
  const [newLike, setNewLike] = useState('');
  const [newDislike, setNewDislike] = useState('');
  const [interestsSaved, setInterestsSaved] = useState(false);

  const [storyChars, setStoryChars] = useState([]);
  const [charsSaved, setCharsSaved] = useState(false);

  const [storyElements, setStoryElements] = useState('');
  const [storyElSaved, setStoryElSaved] = useState(false);

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
      try {
        const int = profile.interests ? JSON.parse(profile.interests) : {};
        setUserLikes(int.likes || []);
        setUserDislikes(int.dislikes || []);
      } catch { setUserLikes([]); setUserDislikes([]); }
      try {
        setStoryChars(profile.life_variables ? JSON.parse(profile.life_variables) : []);
      } catch { setStoryChars([]); }
      setStoryElements(profile.story_elements || '');
    }
  }, [profile]);

  const checkGmailStatus = useCallback(async () => {
    try {
      const status = await api.gmailStatus();
      setGmailConnected(status.connected);
    } catch {
      setGmailConnected(false);
    } finally {
      setGmailLoading(false);
    }
  }, []);

  useEffect(() => {
    checkGcalStatus();
    checkGmailStatus();
    loadKeywords();
    api.getShopItems().then(setShopItems);
  }, [checkGcalStatus, checkGmailStatus, loadKeywords]);

  useEffect(() => {
    if (searchParams.get('gcal') === 'connected') {
      setGcalConnected(true);
      setSyncResult({ message: 'Google Calendar connected!' });
      searchParams.delete('gcal');
      setSearchParams(searchParams, { replace: true });
      setShowSettings(true);
      setShowAdvanced(true);
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

  const handleGmailSync = async () => {
    try {
      setGmailError(null);
      setGmailSyncResult(null);
      setGmailSyncing(true);
      const result = await api.gmailSync();
      setGmailSyncResult(result);
      setGmailConnected(true);
      setTimeout(() => setGmailSyncResult(null), 5000);
    } catch (err) {
      setGmailError(err.message);
    } finally {
      setGmailSyncing(false);
    }
  };

  const addKeyword = (type) => {
    const kw = (type === 'hard' ? newHardKw : newEasyKw).trim().toLowerCase();
    if (!kw) return;
    if (type === 'hard') {
      if (removedHard.includes(kw)) setRemovedHard((prev) => prev.filter((k) => k !== kw));
      else if (!defaultKeywords.hard.includes(kw) && !customHard.includes(kw)) setCustomHard((prev) => [...prev, kw]);
      setNewHardKw('');
    }
    if (type === 'easy') {
      if (removedEasy.includes(kw)) setRemovedEasy((prev) => prev.filter((k) => k !== kw));
      else if (!defaultKeywords.easy.includes(kw) && !customEasy.includes(kw)) setCustomEasy((prev) => [...prev, kw]);
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
      await api.gcalUpdateKeywords({ hard: customHard, easy: customEasy, removed_hard: removedHard, removed_easy: removedEasy });
      setKwSaved(true);
      setTimeout(() => setKwSaved(false), 2000);
    } catch (err) {
      setGcalError(err.message);
    }
  };

  const addInterest = (type) => {
    const val = (type === 'like' ? newLike : newDislike).trim();
    if (!val) return;
    if (type === 'like' && !userLikes.includes(val)) { setUserLikes([...userLikes, val]); setNewLike(''); }
    if (type === 'dislike' && !userDislikes.includes(val)) { setUserDislikes([...userDislikes, val]); setNewDislike(''); }
  };

  const saveInterests = async () => {
    await api.updateProfile({ interests: JSON.stringify({ likes: userLikes, dislikes: userDislikes }) });
    onUpdate();
    setInterestsSaved(true);
    setTimeout(() => setInterestsSaved(false), 2000);
  };

  const updateChar = (idx, field, value) => {
    setStoryChars(storyChars.map((c, i) => i === idx ? { ...c, [field]: value } : c));
  };

  const saveChars = async () => {
    const valid = storyChars.filter((c) => c.name.trim());
    await api.updateProfile({ life_variables: JSON.stringify(valid) });
    onUpdate();
    setCharsSaved(true);
    setTimeout(() => setCharsSaved(false), 2000);
  };

  const handleDevCurrency = async () => {
    await api.devAddCurrency();
    onUpdate();
    setDevUsed(true);
    setTimeout(() => setDevUsed(false), 2000);
  };

  const saveStoryElements = async () => {
    await api.updateProfile({ story_elements: storyElements.trim() || null });
    onUpdate();
    setStoryElSaved(true);
    setTimeout(() => setStoryElSaved(false), 2000);
  };

  if (!profile) return <p>Loading...</p>;

  const xpForNext = 100 * profile.level;
  const xpPercent = Math.min(100, Math.round((profile.xp / xpForNext) * 100));

  const equippedLayers = LAYER_ORDER
    .map((slot) => {
      const itemId = profile[`equipped_${slot}`];
      if (!itemId) return null;
      return shopItems.find((i) => i.id === itemId)?.equipped_image_url ?? null;
    })
    .filter(Boolean);

  return (
    <div>
      <h1>Adventurer Profile</h1>

      {/* ── Avatar ──────────────────────────────────────── */}
      <div className={styles.avatarSection}>
        <div className={styles.avatarFrame}>
          <img src="/images/avatar_base.png" alt="Avatar" className={styles.avatarLayer} />
          {equippedLayers.map((url, i) => (
            <img key={i} src={url} alt="" className={styles.avatarLayer} />
          ))}
        </div>
        <div className={styles.equipSlots}>
          {SLOTS.map((slot) => {
            const itemId = profile[`equipped_${slot}`];
            const item = shopItems.find((i) => i.id === itemId);
            return (
              <div key={slot} className={`${styles.slot} ${item ? styles.slotFilled : ''}`}>
                <span className={styles.slotLabel}>{SLOT_LABELS[slot]}</span>
                <span className={styles.slotItem}>{item ? item.name : '—'}</span>
              </div>
            );
          })}
          <p className={styles.equipHint}>Equip accessories in the Shop</p>
        </div>
      </div>

      {/* ── Stats ───────────────────────────────────────── */}
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

      {/* ── Profile form ────────────────────────────────── */}
      <div className={styles.form}>
        <label>Display Name</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} />

        <label>Story Genre Preference</label>
        <select value={genre} onChange={(e) => setGenre(e.target.value)}>
          {GENRES.map((g) => (
            <option key={g} value={g}>{g.charAt(0).toUpperCase() + g.slice(1)}</option>
          ))}
        </select>

        <div className={styles.formActions}>
          <button className="btn-primary" onClick={handleSave}>Save Profile</button>
          {saved && <span className={styles.saved}>Saved!</span>}
          <button
            className={styles.settingsToggle}
            onClick={() => setShowSettings((s) => !s)}
          >
            ⚙ Settings {showSettings ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {/* ── Settings panel ──────────────────────────────── */}
      {showSettings && (
        <div className={styles.settingsPanel}>

          {/* Interests & Dislikes */}
          <div className={styles.settingsBlock}>
            <h2 className={styles.settingsBlockTitle}>Interests & Dislikes</h2>
            <p className={styles.gcalMuted} style={{ marginBottom: '0.75rem' }}>
              These details shape your AI-generated story adventures.
            </p>
            <div className={styles.kwGroup}>
              <label className={styles.kwLabel}>Things I enjoy</label>
              <div className={styles.kwTags}>
                {userLikes.map((tag, i) => (
                  <span key={i} className={styles.kwTagCustom}>
                    {tag}
                    <button onClick={() => setUserLikes(userLikes.filter((_, j) => j !== i))}>&times;</button>
                  </span>
                ))}
              </div>
              <div className={styles.kwAdd}>
                <input
                  value={newLike}
                  onChange={(e) => setNewLike(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addInterest('like')}
                  placeholder="Add something you enjoy..."
                />
                <button className="btn-primary" onClick={() => addInterest('like')}>+</button>
              </div>
            </div>
            <div className={styles.kwGroup}>
              <label className={styles.kwLabel}>Things I dislike</label>
              <div className={styles.kwTags}>
                {userDislikes.map((tag, i) => (
                  <span key={i} className={styles.kwTagDefault}>
                    {tag}
                    <button onClick={() => setUserDislikes(userDislikes.filter((_, j) => j !== i))}>&times;</button>
                  </span>
                ))}
              </div>
              <div className={styles.kwAdd}>
                <input
                  value={newDislike}
                  onChange={(e) => setNewDislike(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addInterest('dislike')}
                  placeholder="Add something you dislike..."
                />
                <button className="btn-primary" onClick={() => addInterest('dislike')}>+</button>
              </div>
            </div>
            <div className={styles.kwFooter}>
              <button className="btn-primary" onClick={saveInterests}>Save Interests</button>
              {interestsSaved && <span className={styles.saved}>Saved!</span>}
            </div>
          </div>

          {/* Story Characters */}
          <div className={styles.settingsBlock}>
            <h2 className={styles.settingsBlockTitle}>Story Characters</h2>
            <p className={styles.gcalMuted} style={{ marginBottom: '0.75rem' }}>
              People, pets, or entities from your life that may appear in your stories.
            </p>
            {storyChars.map((c, i) => (
              <div key={i} className={styles.charRow}>
                <input
                  className={styles.charField}
                  value={c.name}
                  onChange={(e) => updateChar(i, 'name', e.target.value)}
                  placeholder="Name"
                />
                <select
                  className={styles.charField}
                  value={c.role}
                  onChange={(e) => updateChar(i, 'role', e.target.value)}
                >
                  {CHAR_ROLES.map((r) => (
                    <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                  ))}
                </select>
                <input
                  className={styles.charFieldWide}
                  value={c.description}
                  onChange={(e) => updateChar(i, 'description', e.target.value)}
                  placeholder="Description"
                />
                <button
                  className={styles.charRemove}
                  onClick={() => setStoryChars(storyChars.filter((_, j) => j !== i))}
                >&times;</button>
              </div>
            ))}
            <button
              className={styles.charAddBtn}
              onClick={() => setStoryChars([...storyChars, { name: '', role: 'ally', description: '' }])}
            >+ Add Character</button>
            <div className={styles.kwFooter} style={{ marginTop: '0.75rem' }}>
              <button className="btn-primary" onClick={saveChars}>Save Characters</button>
              {charsSaved && <span className={styles.saved}>Saved!</span>}
            </div>
          </div>

          {/* Story Elements */}
          <div className={styles.settingsBlock}>
            <h2 className={styles.settingsBlockTitle}>Story Elements</h2>
            <p className={styles.gcalMuted} style={{ marginBottom: '0.75rem' }}>
              Describe settings, plotlines, or directions for your AI-generated stories.
            </p>
            <textarea
              className={styles.storyElementsInput}
              value={storyElements}
              onChange={(e) => setStoryElements(e.target.value)}
              placeholder="e.g. I live in a coastal town. I'd love a treasure-hunting plotline. Make the tone lighthearted but with real stakes..."
              rows={5}
            />
            <div className={styles.kwFooter} style={{ marginTop: '0.75rem' }}>
              <button className="btn-primary" onClick={saveStoryElements}>Save Story Elements</button>
              {storyElSaved && <span className={styles.saved}>Saved!</span>}
            </div>
          </div>

          {/* ── Developer tools ─────────────────────────── */}
          <div className={styles.settingsBlock}>
            <h2 className={styles.settingsBlockTitle}>Developer</h2>
            <p className={styles.gcalMuted} style={{ marginBottom: '0.75rem' }}>
              Testing utilities — not for normal use.
            </p>
            <div className={styles.kwFooter}>
              <button className={styles.devBtn} onClick={handleDevCurrency}>
                ⚠ Add +999 Coins & Gems
              </button>
              {devUsed && <span className={styles.saved}>Done!</span>}
            </div>
          </div>

          {/* ── Advanced Settings toggle ─────────────────── */}
          <button
            className={styles.advancedToggle}
            onClick={() => setShowAdvanced((s) => !s)}
          >
            <span>Advanced Settings</span>
            <span className={styles.advancedToggleIcon}>{showAdvanced ? '▲' : '▼'}</span>
          </button>

          {showAdvanced && (
            <div className={styles.advancedPanel}>

              {/* Google Calendar */}
              <div className={styles.settingsBlock}>
                <h2 className={styles.settingsBlockTitle}>Google Calendar</h2>
                {gcalLoading ? (
                  <p className={styles.gcalMuted}>Checking connection...</p>
                ) : gcalConnected ? (
                  <div className={styles.gcalConnected}>
                    <span className={styles.gcalBadge}>Connected</span>
                    <div className={styles.gcalActions}>
                      <button className="btn-primary" onClick={handleGcalSync}>Sync Now</button>
                      <button className={styles.gcalDisconnect} onClick={handleGcalDisconnect}>Disconnect</button>
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
                  <p className={styles.kwHint}>Events matching these words get auto-assigned a difficulty when synced.</p>
                  <div className={styles.kwGroup}>
                    <label className={styles.kwLabel}>Hard keywords</label>
                    <div className={styles.kwTags}>
                      {defaultKeywords.hard.filter((kw) => !removedHard.includes(kw)).map((kw) => (
                        <span key={`dh-${kw}`} className={styles.kwTagDefault}>
                          {kw}<button onClick={() => removeDefaultKeyword('hard', kw)}>&times;</button>
                        </span>
                      ))}
                      {customHard.map((kw, i) => (
                        <span key={`ch-${i}`} className={styles.kwTagCustom}>
                          {kw}<button onClick={() => removeCustomKeyword('hard', i)}>&times;</button>
                        </span>
                      ))}
                    </div>
                    <div className={styles.kwAdd}>
                      <input value={newHardKw} onChange={(e) => setNewHardKw(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && addKeyword('hard')} placeholder="Add hard keyword..." />
                      <button className="btn-primary" onClick={() => addKeyword('hard')}>+</button>
                    </div>
                  </div>
                  <div className={styles.kwGroup}>
                    <label className={styles.kwLabel}>Easy keywords</label>
                    <div className={styles.kwTags}>
                      {defaultKeywords.easy.filter((kw) => !removedEasy.includes(kw)).map((kw) => (
                        <span key={`de-${kw}`} className={styles.kwTagDefault}>
                          {kw}<button onClick={() => removeDefaultKeyword('easy', kw)}>&times;</button>
                        </span>
                      ))}
                      {customEasy.map((kw, i) => (
                        <span key={`ce-${i}`} className={styles.kwTagCustom}>
                          {kw}<button onClick={() => removeCustomKeyword('easy', i)}>&times;</button>
                        </span>
                      ))}
                    </div>
                    <div className={styles.kwAdd}>
                      <input value={newEasyKw} onChange={(e) => setNewEasyKw(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && addKeyword('easy')} placeholder="Add easy keyword..." />
                      <button className="btn-primary" onClick={() => addKeyword('easy')}>+</button>
                    </div>
                  </div>
                  <div className={styles.kwFooter}>
                    <button className="btn-primary" onClick={saveKeywords}>Save Keywords</button>
                    {kwSaved && <span className={styles.saved}>Saved!</span>}
                  </div>
                </div>
              </div>

              {/* Gmail Inbox */}
              <div className={styles.settingsBlock}>
                <h2 className={styles.settingsBlockTitle}>Gmail Inbox</h2>
                {gmailLoading ? (
                  <p className={styles.gcalMuted}>Checking Gmail access...</p>
                ) : gmailConnected ? (
                  <div>
                    <span className={styles.gcalBadge}>Connected</span>
                    <button
                      className="btn-primary"
                      onClick={handleGmailSync}
                      disabled={gmailSyncing}
                      style={{ marginLeft: '0.75rem' }}
                    >
                      {gmailSyncing ? 'Scanning...' : 'Sync Inbox'}
                    </button>
                  </div>
                ) : (
                  <p className={styles.gcalMuted}>
                    Gmail access is granted when you connect Google Calendar.
                    {!gcalConnected && ' Connect Google Calendar above to enable inbox sync.'}
                    {gcalConnected && ' Disconnect and reconnect to grant Gmail permissions.'}
                  </p>
                )}
                {gmailSyncResult && (
                  <div className={styles.gcalResult}>
                    Imported {gmailSyncResult.imported} task{gmailSyncResult.imported !== 1 ? 's' : ''} from inbox,
                    skipped {gmailSyncResult.skipped}.
                  </div>
                )}
                {gmailError && <div className={styles.gcalError}>{gmailError}</div>}
              </div>

            </div>
          )}
        </div>
      )}
    </div>
  );
}
