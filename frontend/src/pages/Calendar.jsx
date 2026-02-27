import { useState, useEffect, useCallback, useMemo } from 'react';
import TaskCard from '../components/TaskCard';
import TaskForm from '../components/TaskForm';
import RewardPopup from '../components/RewardPopup';
import { api } from '../api';
import styles from './Calendar.module.css';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const DAY_LABELS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function getCalendarDays(year, month) {
  const firstOfMonth = new Date(year, month, 1);
  const startDow = firstOfMonth.getDay();
  const gridStart = new Date(year, month, 1 - startDow);

  const days = [];
  for (let i = 0; i < 42; i++) {
    const d = new Date(gridStart);
    d.setDate(gridStart.getDate() + i);
    days.push(d.toISOString().slice(0, 10));
  }
  return days;
}

function formatDateLabel(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

export default function Calendar({ onReward }) {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth());
  const [selectedDate, setSelectedDate] = useState(now.toISOString().slice(0, 10));

  const [tasks, setTasks] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [reward, setReward] = useState(null);

  const today = new Date().toISOString().slice(0, 10);
  const calendarDays = useMemo(() => getCalendarDays(year, month), [year, month]);
  const currentMonthPrefix = `${year}-${String(month + 1).padStart(2, '0')}`;

  const tasksByDate = useMemo(() => {
    const map = {};
    for (const t of tasks) {
      if (t.due_date) {
        if (!map[t.due_date]) map[t.due_date] = [];
        map[t.due_date].push(t);
      }
    }
    return map;
  }, [tasks]);

  const selectedTasks = useMemo(() => {
    return tasksByDate[selectedDate] || [];
  }, [tasksByDate, selectedDate]);

  const load = useCallback(() => {
    api.getTasks().then(setTasks).catch(console.error);
  }, []);

  useEffect(() => { load(); }, [load]);

  const goToPrevMonth = () => {
    if (month === 0) { setMonth(11); setYear(year - 1); }
    else { setMonth(month - 1); }
  };

  const goToNextMonth = () => {
    if (month === 11) { setMonth(0); setYear(year + 1); }
    else { setMonth(month + 1); }
  };

  const goToToday = () => {
    const n = new Date();
    setYear(n.getFullYear());
    setMonth(n.getMonth());
    setSelectedDate(n.toISOString().slice(0, 10));
  };

  const handleSave = async (data) => {
    if (editing) {
      await api.updateTask(editing.id, data);
    } else {
      const payload = { ...data };
      if (!payload.due_date && selectedDate) {
        payload.due_date = selectedDate;
      }
      await api.createTask(payload);
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

  const handleAddOnDate = (dateStr) => {
    setSelectedDate(dateStr);
    setEditing(null);
    setShowForm(true);
  };

  return (
    <div>
      <div className={styles.header}>
        <h1>Quest Calendar</h1>
        <div className={styles.monthNav}>
          <button className="btn-secondary" onClick={goToPrevMonth}>&larr;</button>
          <span className={styles.monthLabel}>
            {MONTH_NAMES[month]} {year}
          </span>
          <button className="btn-secondary" onClick={goToNextMonth}>&rarr;</button>
          <button className="btn-secondary" onClick={goToToday}>Today</button>
        </div>
        <button className="btn-primary" onClick={() => handleAddOnDate(selectedDate)}>
          + New Quest
        </button>
      </div>

      <div className={styles.weekHeader}>
        {DAY_LABELS.map((label) => (
          <div key={label} className={styles.weekDay}>{label}</div>
        ))}
      </div>

      <div className={styles.grid}>
        {calendarDays.map((day) => {
          const isToday = day === today;
          const isSelected = day === selectedDate;
          const isOutside = !day.startsWith(currentMonthPrefix);
          const dayTasks = tasksByDate[day] || [];
          const pendingCount = dayTasks.filter((t) => t.status !== 'completed').length;
          const completedCount = dayTasks.filter((t) => t.status === 'completed').length;
          const dayNum = parseInt(day.slice(8), 10);

          return (
            <div
              key={day}
              className={[
                styles.cell,
                isToday ? styles.today : '',
                isSelected ? styles.selected : '',
                isOutside ? styles.outside : '',
              ].filter(Boolean).join(' ')}
              onClick={() => setSelectedDate(day)}
            >
              <span className={styles.dayNum}>{dayNum}</span>
              {dayTasks.length > 0 && (
                <div className={styles.indicators}>
                  {pendingCount > 0 && (
                    <span className={styles.dotPending}>{pendingCount}</span>
                  )}
                  {completedCount > 0 && (
                    <span className={styles.dotDone}>{completedCount}</span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className={styles.detail}>
        <div className={styles.detailHeader}>
          <h2>{formatDateLabel(selectedDate)}</h2>
          <button className="btn-primary" onClick={() => handleAddOnDate(selectedDate)}>
            + Add Quest
          </button>
        </div>
        {selectedTasks.length === 0 && (
          <p className={styles.empty}>No quests scheduled for this day.</p>
        )}
        {selectedTasks.map((t) => (
          <TaskCard
            key={t.id}
            task={t}
            onComplete={handleComplete}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))}
      </div>

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
