import { useState, useEffect, useCallback } from 'react';
import TaskCard from '../components/TaskCard';
import TaskForm from '../components/TaskForm';
import RewardPopup from '../components/RewardPopup';
import { api } from '../api';
import styles from './Dashboard.module.css';

export default function Dashboard({ onReward }) {
  const [tasks, setTasks] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [reward, setReward] = useState(null);

  const today = new Date().toISOString().slice(0, 10);

  const load = useCallback(() => {
    api.getTasks().then((all) => {
      const todayTasks = all.filter((t) => {
        if (t.due_date === today) return true;
        if (t.due_date && t.due_date < today && t.status !== 'completed') return true;
        if (!t.due_date && t.status !== 'completed') return true;
        return false;
      });
      setTasks(todayTasks);
    });
  }, [today]);

  useEffect(() => { load(); }, [load]);

  const handleSave = async (data) => {
    if (editing) {
      await api.updateTask(editing.id, data);
    } else {
      await api.createTask({ ...data, due_date: data.due_date || today });
    }
    setShowForm(false);
    setEditing(null);
    load();
  };

  const handleComplete = async (id) => {
    const r = await api.completeTask(id);
    setReward(r);
    onReward();
    load();
  };

  const handleDelete = async (id) => {
    await api.deleteTask(id);
    load();
  };

  const handleEdit = (task) => {
    setEditing(task);
    setShowForm(true);
  };

  const pending = tasks.filter((t) => t.status !== 'completed');
  const completed = tasks.filter((t) => t.status === 'completed');

  return (
    <div>
      <div className={styles.header}>
        <h1>Today's Quests</h1>
        <button className="btn-primary" onClick={() => { setEditing(null); setShowForm(true); }}>
          + New Quest
        </button>
      </div>

      {pending.length === 0 && <p className={styles.empty}>No active quests. Add one to get started!</p>}
      {pending.map((t) => (
        <TaskCard key={t.id} task={t} onComplete={handleComplete} onEdit={handleEdit} onDelete={handleDelete} />
      ))}

      {completed.length > 0 && (
        <>
          <h2 className={styles.section}>Completed</h2>
          {completed.map((t) => (
            <TaskCard key={t.id} task={t} onComplete={handleComplete} onEdit={handleEdit} onDelete={handleDelete} />
          ))}
        </>
      )}

      {showForm && (
        <TaskForm
          task={editing}
          onSave={handleSave}
          onCancel={() => { setShowForm(false); setEditing(null); }}
        />
      )}

      {reward && <RewardPopup reward={reward} onClose={() => setReward(null)} />}
    </div>
  );
}
