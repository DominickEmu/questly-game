import { useState, useEffect } from 'react';
import { api } from '../api';
import styles from './Profile.module.css';

const GENRES = ['fantasy', 'sci-fi', 'mystery', 'horror', 'adventure', 'comedy'];

export default function Profile({ profile, onUpdate }) {
  const [username, setUsername] = useState('');
  const [genre, setGenre] = useState('fantasy');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (profile) {
      setUsername(profile.username);
      setGenre(profile.genre_preference);
    }
  }, [profile]);

  const handleSave = async () => {
    await api.updateProfile({ username, genre_preference: genre });
    onUpdate();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
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
          <div className={styles.statValue}>🪙 {profile.coins}</div>
        </div>
        <div className={styles.stat}>
          <div className={styles.statLabel}>Gems</div>
          <div className={styles.statValue}>💎 {profile.gems}</div>
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
