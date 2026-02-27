import { useState, useEffect, useCallback, useMemo } from 'react';
import TaskCard from '../components/TaskCard';
import TaskForm from '../components/TaskForm';
import RewardPopup from '../components/RewardPopup';
import { api } from '../api';
import styles from './Weekly.module.css';

function getWeekDays() {
  const days = [];
  const now = new Date();
  const start = new Date(now);
  start.setDate(now.getDate() - now.getDay());
  for (let i = 0; i < 7; i++) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    days.push(d.toISOString().slice(0, 10));
  }
  return days;
}

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function Weekly({ onReward }) {
  const [tasks, setTasks] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [reward, setReward] = useState(null);
  const weekDays = useMemo(() => getWeekDays(), []);
  const today = new Date().toISOString().slice(0, 10);

  const load = useCallback(() => {
    api.getTasks().then((all) => {
      const weekStart = weekDays[0];
      const weekEnd = weekDays[6];
      setTasks(all.filter((t) => t.due_date && t.due_date >= weekStart && t.due_date <= weekEnd));
    });
  }, [weekDays]);

  useEffect(() => { load(); }, [load]);

  const handleSave = async (data) => {
    if (editing) {
      await api.updateTask(editing.id, data);
    } else {
      await api.createTask(data);
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

  return (
    <div>
      <div className={styles.header}>
        <h1>Weekly Quest Board</h1>
        <button className="btn-primary" onClick={() => { setEditing(null); setShowForm(true); }}>
          + New Quest
        </button>
      </div>

      {weekDays.map((day, i) => {
        const dayTasks = tasks.filter((t) => t.due_date === day);
        const isToday = day === today;
        return (
          <div key={day} className={`${styles.day} ${isToday ? styles.today : ''}`}>
            <h2>{DAY_LABELS[i]} — {day}</h2>
            {dayTasks.length === 0 && <p className={styles.empty}>No quests</p>}
            {dayTasks.map((t) => (
              <TaskCard key={t.id} task={t} onComplete={handleComplete} onEdit={handleEdit} onDelete={handleDelete} />
            ))}
          </div>
        );
      })}

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
