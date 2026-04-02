import { useState } from 'react';
import { api } from '../api';
import styles from './Onboarding.module.css';

const GENRES = [
  { id: 'fantasy', label: 'Fantasy', desc: 'Magic, swords, and ancient prophecies' },
  { id: 'sci-fi', label: 'Sci-Fi', desc: 'Advanced technology and futuristic societies' },
  { id: 'mystery', label: 'Mystery', desc: 'Clues, suspense, and unexpected twists' },
  { id: 'horror', label: 'Horror', desc: 'Creeping dread and supernatural threats' },
  { id: 'adventure', label: 'Adventure', desc: 'Daring escapades and treasure hunts' },
  { id: 'comedy', label: 'Comedy', desc: 'Witty banter and lighthearted chaos' },
];

const ROLES = ['ally', 'rival', 'mentor', 'companion', 'antagonist', 'wildcard'];

const TOTAL_STEPS = 6;

export default function Onboarding({ onUpdate }) {
  const [step, setStep] = useState(1);
  const [username, setUsername] = useState('');
  const [genre, setGenre] = useState('fantasy');
  const [likes, setLikes] = useState([]);
  const [dislikes, setDislikes] = useState([]);
  const [likeInput, setLikeInput] = useState('');
  const [dislikeInput, setDislikeInput] = useState('');
  const [characters, setCharacters] = useState([{ name: '', role: 'ally', description: '' }]);
  const [storyElements, setStoryElements] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Live theme preview
  const applyTheme = (g) => {
    if (g === 'fantasy') {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', g);
    }
  };

  const selectGenre = (g) => {
    setGenre(g);
    applyTheme(g);
  };

  const addTag = (type) => {
    const input = type === 'like' ? likeInput : dislikeInput;
    const tag = input.trim();
    if (!tag) return;
    if (type === 'like' && !likes.includes(tag)) {
      setLikes([...likes, tag]);
      setLikeInput('');
    }
    if (type === 'dislike' && !dislikes.includes(tag)) {
      setDislikes([...dislikes, tag]);
      setDislikeInput('');
    }
  };

  const removeTag = (type, idx) => {
    if (type === 'like') setLikes(likes.filter((_, i) => i !== idx));
    if (type === 'dislike') setDislikes(dislikes.filter((_, i) => i !== idx));
  };

  const updateCharacter = (idx, field, value) => {
    setCharacters(characters.map((c, i) => i === idx ? { ...c, [field]: value } : c));
  };

  const addCharacter = () => {
    setCharacters([...characters, { name: '', role: 'ally', description: '' }]);
  };

  const removeCharacter = (idx) => {
    setCharacters(characters.filter((_, i) => i !== idx));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const validChars = characters.filter((c) => c.name.trim());
      await api.updateProfile({
        username: username.trim() || 'Adventurer',
        genre_preference: genre,
        interests: JSON.stringify({ likes, dislikes }),
        life_variables: JSON.stringify(validChars),
        story_elements: storyElements.trim() || null,
        setup_complete: true,
      });
      onUpdate();
    } catch (err) {
      console.error(err);
      setSubmitting(false);
    }
  };

  const canNext = () => {
    if (step === 1) return username.trim().length > 0;
    return true;
  };

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        {/* Progress */}
        <div className={styles.progress}>
          {Array.from({ length: TOTAL_STEPS }, (_, i) => (
            <div
              key={i}
              className={`${styles.dot} ${i + 1 <= step ? styles.dotActive : ''}`}
            />
          ))}
        </div>

        {/* Step 1: Name */}
        {step === 1 && (
          <div className={styles.stepContent}>
            <h1 className={styles.title}>Name Your Adventurer</h1>
            <p className={styles.subtitle}>Every legend begins with a name...</p>
            <input
              className={styles.nameInput}
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your name"
              maxLength={30}
              onKeyDown={(e) => e.key === 'Enter' && canNext() && setStep(2)}
              autoFocus
            />
          </div>
        )}

        {/* Step 2: Genre */}
        {step === 2 && (
          <div className={styles.stepContent}>
            <h1 className={styles.title}>Choose Your Realm</h1>
            <p className={styles.subtitle}>This shapes the tone of your story adventures</p>
            <div className={styles.genreGrid}>
              {GENRES.map((g) => (
                <button
                  key={g.id}
                  className={`${styles.genreCard} ${genre === g.id ? styles.genreSelected : ''}`}
                  onClick={() => selectGenre(g.id)}
                >
                  <span className={styles.genreName}>{g.label}</span>
                  <span className={styles.genreDesc}>{g.desc}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Interests & Dislikes */}
        {step === 3 && (
          <div className={styles.stepContent}>
            <h1 className={styles.title}>Tell Us About Yourself</h1>
            <p className={styles.subtitle}>These shape how your story adventures feel</p>

            <div className={styles.tagSection}>
              <label className={styles.tagLabel}>Things you enjoy</label>
              <div className={styles.tags}>
                {likes.map((tag, i) => (
                  <span key={i} className={styles.tag}>
                    {tag}
                    <button onClick={() => removeTag('like', i)}>&times;</button>
                  </span>
                ))}
              </div>
              <div className={styles.tagInputRow}>
                <input
                  value={likeInput}
                  onChange={(e) => setLikeInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addTag('like')}
                  placeholder="e.g. hiking, cooking, video games..."
                />
                <button className="btn-primary" onClick={() => addTag('like')}>+</button>
              </div>
            </div>

            <div className={styles.tagSection}>
              <label className={styles.tagLabel}>Things you dislike</label>
              <div className={styles.tags}>
                {dislikes.map((tag, i) => (
                  <span key={i} className={`${styles.tag} ${styles.tagDislike}`}>
                    {tag}
                    <button onClick={() => removeTag('dislike', i)}>&times;</button>
                  </span>
                ))}
              </div>
              <div className={styles.tagInputRow}>
                <input
                  value={dislikeInput}
                  onChange={(e) => setDislikeInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addTag('dislike')}
                  placeholder="e.g. mornings, paperwork, spiders..."
                />
                <button className="btn-primary" onClick={() => addTag('dislike')}>+</button>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Life Variables */}
        {step === 4 && (
          <div className={styles.stepContent}>
            <h1 className={styles.title}>Allies & Rivals</h1>
            <p className={styles.subtitle}>
              Add people, pets, or entities from your life. They may appear as characters in your story.
            </p>

            <div className={styles.charList}>
              {characters.map((c, i) => (
                <div key={i} className={styles.charRow}>
                  <input
                    className={styles.charName}
                    value={c.name}
                    onChange={(e) => updateCharacter(i, 'name', e.target.value)}
                    placeholder="Name"
                  />
                  <select
                    className={styles.charRole}
                    value={c.role}
                    onChange={(e) => updateCharacter(i, 'role', e.target.value)}
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                    ))}
                  </select>
                  <input
                    className={styles.charDesc}
                    value={c.description}
                    onChange={(e) => updateCharacter(i, 'description', e.target.value)}
                    placeholder="Description (e.g. Mark from accounting)"
                  />
                  {characters.length > 1 && (
                    <button className={styles.charRemove} onClick={() => removeCharacter(i)}>&times;</button>
                  )}
                </div>
              ))}
            </div>
            <button className={styles.addCharBtn} onClick={addCharacter}>+ Add Character</button>
          </div>
        )}

        {/* Step 5: Story Elements */}
        {step === 5 && (
          <div className={styles.stepContent}>
            <h1 className={styles.title}>Extra Story Elements</h1>
            <p className={styles.subtitle}>
              Optionally describe settings, plotlines, or directions you'd like your AI stories to follow.
            </p>
            <textarea
              className={styles.storyElementsInput}
              value={storyElements}
              onChange={(e) => setStoryElements(e.target.value)}
              placeholder={"e.g. I live in a coastal town. I'd love a treasure-hunting plotline. Make the tone lighthearted but with real stakes..."}
              rows={6}
            />
          </div>
        )}

        {/* Step 6: Summary */}
        {step === 6 && (
          <div className={styles.stepContent}>
            <h1 className={styles.title}>Ready to Begin</h1>
            <div className={styles.summary}>
              <div className={styles.summaryRow}>
                <span className={styles.summaryLabel}>Name</span>
                <span className={styles.summaryValue}>{username || 'Adventurer'}</span>
              </div>
              <div className={styles.summaryRow}>
                <span className={styles.summaryLabel}>Realm</span>
                <span className={styles.summaryValue}>{GENRES.find((g) => g.id === genre)?.label}</span>
              </div>
              {likes.length > 0 && (
                <div className={styles.summaryRow}>
                  <span className={styles.summaryLabel}>Enjoys</span>
                  <span className={styles.summaryValue}>{likes.join(', ')}</span>
                </div>
              )}
              {dislikes.length > 0 && (
                <div className={styles.summaryRow}>
                  <span className={styles.summaryLabel}>Dislikes</span>
                  <span className={styles.summaryValue}>{dislikes.join(', ')}</span>
                </div>
              )}
              {characters.filter((c) => c.name.trim()).length > 0 && (
                <div className={styles.summaryRow}>
                  <span className={styles.summaryLabel}>Characters</span>
                  <span className={styles.summaryValue}>
                    {characters.filter((c) => c.name.trim()).map((c) => `${c.name} (${c.role})`).join(', ')}
                  </span>
                </div>
              )}
              {storyElements.trim() && (
                <div className={styles.summaryRow}>
                  <span className={styles.summaryLabel}>Story Elements</span>
                  <span className={styles.summaryValue}>{storyElements.trim()}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className={styles.nav}>
          {step > 1 && (
            <button className="btn-secondary" onClick={() => setStep(step - 1)}>Back</button>
          )}
          <div className={styles.navSpacer} />
          {step < TOTAL_STEPS ? (
            <button
              className="btn-primary"
              onClick={() => setStep(step + 1)}
              disabled={!canNext()}
            >
              Next
            </button>
          ) : (
            <button
              className={styles.startBtn}
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? 'Starting...' : 'Begin Your Quest'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
