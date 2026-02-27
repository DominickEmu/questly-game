import { useState, useEffect } from 'react';
import styles from './TaskForm.module.css';

const EMPTY = {
  title: '',
  description: '',
  difficulty: 'medium',
  category: '',
  due_date: '',
  recurrence: 'none',
};

export default function TaskForm({ task, onSave, onCancel }) {
  const [form, setForm] = useState(EMPTY);

  useEffect(() => {
    if (task) {
      setForm({
        title: task.title || '',
        description: task.description || '',
        difficulty: task.difficulty || 'medium',
        category: task.category || '',
        due_date: task.due_date || '',
        recurrence: task.recurrence || 'none',
      });
    } else {
      setForm(EMPTY);
    }
  }, [task]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    const data = { ...form };
    if (!data.due_date) data.due_date = null;
    if (!data.category) data.category = null;
    if (!data.description) data.description = null;
    onSave(data);
  };

  return (
    <div className={styles.overlay} onClick={onCancel}>
      <form className={styles.form} onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h2>{task ? 'Edit Quest' : 'New Quest'}</h2>

        <label>Title *</label>
        <input name="title" value={form.title} onChange={handleChange} placeholder="What needs to be done?" autoFocus />

        <label>Description</label>
        <textarea name="description" value={form.description} onChange={handleChange} rows={2} placeholder="Optional details..." />

        <div className={styles.row}>
          <div>
            <label>Difficulty</label>
            <select name="difficulty" value={form.difficulty} onChange={handleChange}>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
              <option value="extreme">Extreme</option>
            </select>
          </div>
          <div>
            <label>Recurrence</label>
            <select name="recurrence" value={form.recurrence} onChange={handleChange}>
              <option value="none">None</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </div>
        </div>

        <div className={styles.row}>
          <div>
            <label>Category</label>
            <input name="category" value={form.category} onChange={handleChange} placeholder="e.g. homework" />
          </div>
          <div>
            <label>Due Date</label>
            <input type="date" name="due_date" value={form.due_date} onChange={handleChange} />
          </div>
        </div>

        <div className={styles.buttons}>
          <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>
          <button type="submit" className="btn-primary">{task ? 'Save' : 'Create Quest'}</button>
        </div>
      </form>
    </div>
  );
}
