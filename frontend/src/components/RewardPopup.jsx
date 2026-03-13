import styles from './RewardPopup.module.css';

export default function RewardPopup({ reward, onClose }) {
  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.popup} onClick={(e) => e.stopPropagation()}>
        <h2>Quest Complete!</h2>
        <div className={styles.rewards}>
          <div className={styles.item}>
            <span className={styles.icon}>⚡</span>
            <span>+{reward.xp} XP</span>
          </div>
          <div className={styles.item}>
            <span className={styles.icon}>🪙</span>
            <span>+{reward.coins} Coins</span>
          </div>
          {reward.gems > 0 && (
            <div className={styles.item}>
              <span className={styles.icon}>💎</span>
              <span>+{reward.gems} Gems</span>
            </div>
          )}
        </div>
        {reward.leveled_up && (
          <div className={styles.levelUp}>Level Up! You are now Level {reward.new_level}!</div>
        )}
        {reward.next_task_id && (
          <div className={styles.nextQuest}>Next quest has been queued</div>
        )}
        {reward.story && (
          <div className={styles.storyBox}>
            <div className={styles.storyLabel}>Your tale continues...</div>
            <div className={styles.storyText}>{reward.story}</div>
          </div>
        )}
        <button className="btn-primary" onClick={onClose}>Awesome!</button>
      </div>
    </div>
  );
}
