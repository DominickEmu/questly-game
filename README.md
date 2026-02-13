# questly-game
A game for DH301 that makes a storyline and RPG out of your todo list.

## Elven Quest Journal - Task Tracker

A beautiful, Tolkien-inspired task tracking application with a fantasy elf journal aesthetic.

### Features

- **Task Management**: Create, edit, delete, and mark tasks as complete
- **Custom Labels**: Create your own labels/tags with emoji symbols and colors
- **Label Filtering**: Filter tasks by label to see only relevant quests
- **Fantasy UI**: Beautiful parchment-style interface with elven theming
- **Data Persistence**: All tasks and labels are automatically saved to `quest_journal.json`

### Requirements

The application uses only Python's built-in libraries:
- `tkinter` (usually included with Python)
- `json` (built-in)
- `os` (built-in)
- `datetime` (built-in)

### Running the Application

```bash
python task_tracker.py
```

### Usage

1. **Adding Labels**: Click "➕ Add Label" to create custom labels with emoji symbols
2. **Adding Tasks**: Click "➕ New Quest" to add a new task/quest
3. **Filtering**: Select a label and click "🔍 Filter by Label" to see only tasks with that label
4. **Completing Tasks**: Select a task and click "✅ Complete" to mark it as done
5. **Editing**: Select any task or label and click the respective "✏️ Edit" button

### Data Storage

All data is saved in `quest_journal.json` in the same directory as the application. This file is automatically created and updated when you make changes.