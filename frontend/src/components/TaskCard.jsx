import styles from './TaskCard.module.css';

const DIFF_COLORS = {
  easy: '#2d8a2d',
  medium: '#b8860b',
  hard: '#a83028',
  extreme: '#6b2d8b',
};

export default function TaskCard({ task, onComplete, onEdit, onDelete }) {
  const done = task.status === 'completed';

  return (
    <div className={`${styles.card} ${done ? styles.done : ''}`}>
      <div className={styles.left}>
        <div className={styles.badges}>
          <span
            className={styles.diff}
            style={{ background: DIFF_COLORS[task.difficulty] || '#888' }}
          >
            {task.difficulty}
          </span>
          {task.recurrence !== 'none' && (
            <span className={styles.recurrence}>
              {task.recurrence === 'daily' ? 'Daily' : 'Weekly'}
            </span>
          )}
          {task.story_ender && (
            <span className={styles.storyEnder}>Story ender</span>
          )}
        </div>
        <div>
          <div className={styles.title}>{task.title}</div>
          {task.description && <div className={styles.desc}>{task.description}</div>}
          <div className={styles.meta}>
            {task.category && <span>#{task.category}</span>}
            {task.due_date && <span>Due: {task.due_date}</span>}
          </div>
        </div>
      </div>
      <div className={styles.actions}>
        {!done && (
          <button className="btn-success" onClick={() => onComplete(task.id)}>
            Complete
          </button>
        )}
        {!done && (
          <button className="btn-secondary" onClick={() => onEdit(task)}>
            Edit
          </button>
        )}
        <button className="btn-danger" onClick={() => onDelete(task.id)}>
          Delete
        </button>
      </div>
    </div>
  );
}
