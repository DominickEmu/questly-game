import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class Task:
    def __init__(self, title: str, description: str = "", labels: List[str] = None, completed: bool = False):
        self.title = title
        self.description = description
        self.labels = labels if labels else []
        self.completed = completed
        self.created_at = datetime.now().isoformat()
        self.id = datetime.now().timestamp()
    
    def to_dict(self):
        return {
            'title': self.title,
            'description': self.description,
            'labels': self.labels,
            'completed': self.completed,
            'created_at': self.created_at,
            'id': self.id
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        task = cls(
            title=data['title'],
            description=data.get('description', ''),
            labels=data.get('labels', []),
            completed=data.get('completed', False)
        )
        task.created_at = data.get('created_at', datetime.now().isoformat())
        task.id = data.get('id', datetime.now().timestamp())
        return task

class Label:
    def __init__(self, name: str, symbol: str = "📋", color: str = "#8B7355"):
        self.name = name
        self.symbol = symbol
        self.color = color
    
    def to_dict(self):
        return {
            'name': self.name,
            'symbol': self.symbol,
            'color': self.color
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            name=data['name'],
            symbol=data.get('symbol', '📋'),
            color=data.get('color', '#8B7355')
        )

class TaskTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Elven Quest Journal")
        self.root.geometry("1000x700")
        
        # Data storage
        self.tasks: List[Task] = []
        self.labels: Dict[str, Label] = {}
        self.filter_label: Optional[str] = None
        self.label_index_map: Dict[int, str] = {}
        
        # Load data
        self.load_data()
        
        # Setup UI
        self.setup_ui()
        self.update_task_list()
        self.update_label_list()
    
    def setup_ui(self):
        # Clear existing widgets if rebuilding
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Configure fantasy color scheme
        self.bg_color = "#2C1810"  # Dark brown parchment
        self.paper_color = "#F4E4BC"  # Aged paper
        self.text_color = "#3D2817"  # Dark brown ink
        self.accent_color = "#8B4513"  # Saddle brown
        self.gold_color = "#D4AF37"  # Elven gold
        self.green_color = "#4A7C59"  # Forest green
        
        self.root.configure(bg=self.bg_color)
        
        # Main container with parchment effect
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with fantasy styling
        title_frame = tk.Frame(main_frame, bg=self.bg_color)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            title_frame,
            text="📜 Elven Quest Journal 📜",
            font=("Times New Roman", 24, "bold"),
            bg=self.bg_color,
            fg=self.gold_color
        )
        title_label.pack()
        
        subtitle = tk.Label(
            title_frame,
            text="Chronicle of Tasks and Endeavors",
            font=("Times New Roman", 12, "italic"),
            bg=self.bg_color,
            fg=self.paper_color
        )
        subtitle.pack()
        
        # Content area with two columns
        content_frame = tk.Frame(main_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Labels
        left_panel = tk.Frame(content_frame, bg=self.paper_color, relief=tk.RAISED, bd=3)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), expand=False, ipadx=10, ipady=10)
        left_panel.config(width=250)
        
        label_title = tk.Label(
            left_panel,
            text="🏷️ Labels & Symbols",
            font=("Times New Roman", 14, "bold"),
            bg=self.paper_color,
            fg=self.text_color
        )
        label_title.pack(pady=(0, 10))
        
        # Label list with scrollbar
        label_list_frame = tk.Frame(left_panel, bg=self.paper_color)
        label_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.label_listbox = tk.Listbox(
            label_list_frame,
            font=("Times New Roman", 11),
            bg=self.paper_color,
            fg=self.text_color,
            selectbackground=self.green_color,
            selectforeground="white",
            relief=tk.FLAT,
            bd=2
        )
        self.label_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        label_scrollbar = tk.Scrollbar(label_list_frame, orient=tk.VERTICAL, command=self.label_listbox.yview)
        label_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.label_listbox.config(yscrollcommand=label_scrollbar.set)
        
        # Store mapping of listbox index to label name for easier lookup
        self.label_index_map = {}
        
        # Label buttons
        label_btn_frame = tk.Frame(left_panel, bg=self.paper_color)
        label_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        add_label_btn = tk.Button(
            label_btn_frame,
            text="➕ Add Label",
            command=self.add_label,
            font=("Times New Roman", 10),
            bg=self.green_color,
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        add_label_btn.pack(fill=tk.X, pady=2)
        
        edit_label_btn = tk.Button(
            label_btn_frame,
            text="✏️ Edit Label",
            command=self.edit_label,
            font=("Times New Roman", 10),
            bg=self.accent_color,
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        edit_label_btn.pack(fill=tk.X, pady=2)
        
        delete_label_btn = tk.Button(
            label_btn_frame,
            text="🗑️ Delete Label",
            command=self.delete_label,
            font=("Times New Roman", 10),
            bg="#8B0000",
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        delete_label_btn.pack(fill=tk.X, pady=2)
        
        filter_btn = tk.Button(
            label_btn_frame,
            text="🔍 Filter by Label",
            command=self.filter_by_label,
            font=("Times New Roman", 10),
            bg=self.gold_color,
            fg=self.text_color,
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        filter_btn.pack(fill=tk.X, pady=2)
        
        clear_filter_btn = tk.Button(
            label_btn_frame,
            text="🌐 Show All",
            command=self.clear_filter,
            font=("Times New Roman", 10),
            bg=self.accent_color,
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        clear_filter_btn.pack(fill=tk.X, pady=2)
        
        # Right panel - Tasks
        right_panel = tk.Frame(content_frame, bg=self.paper_color, relief=tk.RAISED, bd=3)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipadx=10, ipady=10)
        
        task_title_frame = tk.Frame(right_panel, bg=self.paper_color)
        task_title_frame.pack(fill=tk.X, pady=(0, 10))
        
        task_title = tk.Label(
            task_title_frame,
            text="📋 Quests & Tasks",
            font=("Times New Roman", 14, "bold"),
            bg=self.paper_color,
            fg=self.text_color
        )
        task_title.pack(side=tk.LEFT)
        
        if self.filter_label:
            filter_indicator = tk.Label(
                task_title_frame,
                text=f"🔍 Filtered: {self.labels[self.filter_label].symbol} {self.filter_label}",
                font=("Times New Roman", 10, "italic"),
                bg=self.paper_color,
                fg=self.green_color
            )
            filter_indicator.pack(side=tk.RIGHT)
        
        # Task list with scrollbar
        task_list_frame = tk.Frame(right_panel, bg=self.paper_color)
        task_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.task_listbox = tk.Listbox(
            task_list_frame,
            font=("Times New Roman", 11),
            bg=self.paper_color,
            fg=self.text_color,
            selectbackground=self.green_color,
            selectforeground="white",
            relief=tk.FLAT,
            bd=2,
            height=15
        )
        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        task_scrollbar = tk.Scrollbar(task_list_frame, orient=tk.VERTICAL, command=self.task_listbox.yview)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_listbox.config(yscrollcommand=task_scrollbar.set)
        
        # Task buttons
        task_btn_frame = tk.Frame(right_panel, bg=self.paper_color)
        task_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        add_task_btn = tk.Button(
            task_btn_frame,
            text="➕ New Quest",
            command=self.add_task,
            font=("Times New Roman", 10),
            bg=self.green_color,
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        add_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        edit_task_btn = tk.Button(
            task_btn_frame,
            text="✏️ Edit Quest",
            command=self.edit_task,
            font=("Times New Roman", 10),
            bg=self.accent_color,
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        edit_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        complete_task_btn = tk.Button(
            task_btn_frame,
            text="✅ Complete",
            command=self.toggle_complete,
            font=("Times New Roman", 10),
            bg=self.gold_color,
            fg=self.text_color,
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        complete_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        delete_task_btn = tk.Button(
            task_btn_frame,
            text="🗑️ Delete",
            command=self.delete_task,
            font=("Times New Roman", 10),
            bg="#8B0000",
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        delete_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
    
    def add_task(self):
        dialog = TaskDialog(self.root, "Add New Quest", labels=list(self.labels.keys()))
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            title, description, selected_labels = dialog.result
            task = Task(title, description, selected_labels)
            self.tasks.append(task)
            self.update_task_list()
            self.save_data()
    
    def edit_task(self):
        selection = self.task_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a quest to edit.")
            return
        
        task = self.get_selected_task()
        if not task:
            return
        
        dialog = TaskDialog(
            self.root,
            "Edit Quest",
            labels=list(self.labels.keys()),
            initial_title=task.title,
            initial_description=task.description,
            initial_labels=task.labels
        )
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            title, description, selected_labels = dialog.result
            task.title = title
            task.description = description
            task.labels = selected_labels
            self.update_task_list()
            self.save_data()
    
    def delete_task(self):
        selection = self.task_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a quest to delete.")
            return
        
        task = self.get_selected_task()
        if not task:
            return
        
        if messagebox.askyesno("Confirm", f"Remove quest '{task.title}' from the journal?"):
            self.tasks.remove(task)
            self.update_task_list()
            self.save_data()
    
    def toggle_complete(self):
        selection = self.task_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a quest to mark.")
            return
        
        task = self.get_selected_task()
        if not task:
            return
        
        task.completed = not task.completed
        self.update_task_list()
        self.save_data()
    
    def get_selected_task(self) -> Optional[Task]:
        selection = self.task_listbox.curselection()
        if not selection:
            return None
        
        index = selection[0]
        filtered_tasks = self.get_filtered_tasks()
        if 0 <= index < len(filtered_tasks):
            return filtered_tasks[index]
        return None
    
    def get_filtered_tasks(self) -> List[Task]:
        if self.filter_label:
            return [t for t in self.tasks if self.filter_label in t.labels]
        return self.tasks
    
    def update_task_list(self):
        if not hasattr(self, 'task_listbox'):
            return
        self.task_listbox.delete(0, tk.END)
        filtered_tasks = self.get_filtered_tasks()
        
        for task in filtered_tasks:
            # Build display string with labels
            label_str = " ".join([self.labels[label].symbol for label in task.labels if label in self.labels])
            if label_str:
                label_str = label_str + " "
            status = "✅" if task.completed else "⭕"
            display = f"{status} {label_str}{task.title}"
            if task.description:
                display += f" - {task.description[:30]}..."
            
            self.task_listbox.insert(tk.END, display)
            
            # Style completed tasks differently
            if task.completed:
                idx = self.task_listbox.size() - 1
                self.task_listbox.itemconfig(idx, {'fg': '#888888'})
    
    def add_label(self):
        dialog = LabelDialog(self.root, "Add New Label")
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            name, symbol, color = dialog.result
            if name in self.labels:
                messagebox.showwarning("Duplicate", f"Label '{name}' already exists.")
                return
            
            self.labels[name] = Label(name, symbol, color)
            self.update_label_list()
            self.save_data()
    
    def edit_label(self):
        selection = self.label_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a label to edit.")
            return
        
        # Get label name from index map
        index = selection[0]
        label_name = self.label_index_map.get(index)
        
        if not label_name:
            # Fallback: extract from display text
            display_text = self.label_listbox.get(index)
            for name, label in self.labels.items():
                if display_text.startswith(f"{label.symbol} {name}"):
                    label_name = name
                    break
        
        label = self.labels.get(label_name)
        if not label:
            return
        
        dialog = LabelDialog(
            self.root,
            "Edit Label",
            initial_name=label.name,
            initial_symbol=label.symbol,
            initial_color=label.color
        )
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            name, symbol, color = dialog.result
            # If name changed, update references in tasks
            if name != label.name:
                for task in self.tasks:
                    if label.name in task.labels:
                        task.labels.remove(label.name)
                        task.labels.append(name)
                del self.labels[label.name]
            
            self.labels[name] = Label(name, symbol, color)
            self.update_label_list()
            self.update_task_list()
            self.save_data()
    
    def delete_label(self):
        selection = self.label_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a label to delete.")
            return
        
        # Get label name from index map
        index = selection[0]
        label_name = self.label_index_map.get(index)
        
        if not label_name:
            # Fallback: extract from display text
            display_text = self.label_listbox.get(index)
            for name, label in self.labels.items():
                if display_text.startswith(f"{label.symbol} {name}"):
                    label_name = name
                    break
        
        label = self.labels.get(label_name)
        if not label:
            return
        
        # Check if label is used in tasks
        used_in = [t.title for t in self.tasks if label_name in t.labels]
        if used_in:
            msg = f"Label '{label_name}' is used in {len(used_in)} quest(s). Remove it from all quests?"
            if not messagebox.askyesno("Label in Use", msg):
                return
            
            # Remove label from all tasks
            for task in self.tasks:
                if label_name in task.labels:
                    task.labels.remove(label_name)
        
        del self.labels[label_name]
        if self.filter_label == label_name:
            self.filter_label = None
        
        self.update_label_list()
        self.update_task_list()
        self.save_data()
    
    def filter_by_label(self):
        selection = self.label_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a label to filter by.")
            return
        
        # Get label name from index map
        index = selection[0]
        label_name = self.label_index_map.get(index)
        
        if not label_name:
            # Fallback: extract from display text
            display_text = self.label_listbox.get(index)
            for name, label in self.labels.items():
                if display_text.startswith(f"{label.symbol} {name}"):
                    label_name = name
                    break
        
        if label_name and label_name in self.labels:
            self.filter_label = label_name
            self.setup_ui()  # Rebuild UI to show filter indicator
            self.update_task_list()
    
    def clear_filter(self):
        self.filter_label = None
        self.setup_ui()
        self.update_task_list()
    
    def update_label_list(self):
        if not hasattr(self, 'label_listbox'):
            return
        self.label_listbox.delete(0, tk.END)
        self.label_index_map = {}
        for idx, (name, label) in enumerate(sorted(self.labels.items())):
            display = f"{label.symbol} {name} - {label.color}"
            self.label_listbox.insert(tk.END, display)
            self.label_index_map[idx] = name
    
    def save_data(self):
        data = {
            'tasks': [task.to_dict() for task in self.tasks],
            'labels': {name: label.to_dict() for name, label in self.labels.items()}
        }
        with open('quest_journal.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_data(self):
        if os.path.exists('quest_journal.json'):
            try:
                with open('quest_journal.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.tasks = [Task.from_dict(t) for t in data.get('tasks', [])]
                self.labels = {name: Label.from_dict(l) for name, l in data.get('labels', {}).items()}
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load journal: {e}")


class TaskDialog:
    def __init__(self, parent, title, labels=None, initial_title="", initial_description="", initial_labels=None):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x450")
        self.dialog.configure(bg="#2C1810")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (450 // 2)
        self.dialog.geometry(f"500x450+{x}+{y}")
        
        main_frame = tk.Frame(self.dialog, bg="#F4E4BC", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        tk.Label(
            main_frame,
            text="Title:",
            font=("Times New Roman", 11, "bold"),
            bg="#F4E4BC",
            fg="#3D2817"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.title_entry = tk.Entry(main_frame, font=("Times New Roman", 11), width=50)
        self.title_entry.pack(fill=tk.X, pady=(0, 15))
        self.title_entry.insert(0, initial_title)
        
        # Description
        tk.Label(
            main_frame,
            text="Description:",
            font=("Times New Roman", 11, "bold"),
            bg="#F4E4BC",
            fg="#3D2817"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.desc_text = tk.Text(main_frame, font=("Times New Roman", 11), width=50, height=8)
        self.desc_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        self.desc_text.insert("1.0", initial_description)
        
        # Labels
        tk.Label(
            main_frame,
            text="Labels:",
            font=("Times New Roman", 11, "bold"),
            bg="#F4E4BC",
            fg="#3D2817"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        label_frame = tk.Frame(main_frame, bg="#F4E4BC")
        label_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        if not labels:
            no_labels = tk.Label(
                label_frame,
                text="No labels available. Create labels first!",
                font=("Times New Roman", 9, "italic"),
                bg="#F4E4BC",
                fg="#888888"
            )
            no_labels.pack(anchor=tk.W, pady=5)
        
        self.label_vars = {}
        if labels:
            # Create a scrollable frame for labels if there are many
            label_canvas = tk.Canvas(label_frame, bg="#F4E4BC", highlightthickness=0, height=100)
            label_scrollbar = tk.Scrollbar(label_frame, orient=tk.VERTICAL, command=label_canvas.yview)
            label_scrollable_frame = tk.Frame(label_canvas, bg="#F4E4BC")
            
            def configure_scroll_region(e):
                label_canvas.configure(scrollregion=label_canvas.bbox("all"))
            
            label_scrollable_frame.bind("<Configure>", configure_scroll_region)
            
            label_canvas_window = label_canvas.create_window((0, 0), window=label_scrollable_frame, anchor="nw")
            label_canvas.configure(yscrollcommand=label_scrollbar.set)
            
            def configure_canvas_width(e):
                canvas_width = e.width
                label_canvas.itemconfig(label_canvas_window, width=canvas_width)
            
            label_canvas.bind('<Configure>', configure_canvas_width)
            
            for label_name in labels:
                var = tk.BooleanVar()
                var.set(label_name in (initial_labels or []))
                self.label_vars[label_name] = var
                
                check = tk.Checkbutton(
                    label_scrollable_frame,
                    text=label_name,
                    variable=var,
                    font=("Times New Roman", 10),
                    bg="#F4E4BC",
                    fg="#3D2817",
                    selectcolor="#F4E4BC",
                    activebackground="#F4E4BC"
                )
                check.pack(anchor=tk.W, pady=2)
            
            label_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            label_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg="#F4E4BC")
        btn_frame.pack(fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Save",
            command=self.save,
            font=("Times New Roman", 10),
            bg="#4A7C59",
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.dialog.destroy,
            font=("Times New Roman", 10),
            bg="#8B0000",
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=5)
        
        self.dialog.focus_set()
        self.title_entry.focus_set()
        self.title_entry.select_range(0, tk.END)
    
    def save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Invalid", "Quest title cannot be empty.")
            return
        
        description = self.desc_text.get("1.0", tk.END).strip()
        selected_labels = [name for name, var in self.label_vars.items() if var.get()]
        
        self.result = (title, description, selected_labels)
        self.dialog.destroy()


class LabelDialog:
    def __init__(self, parent, title, initial_name="", initial_symbol="📋", initial_color="#8B7355"):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.configure(bg="#2C1810")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        main_frame = tk.Frame(self.dialog, bg="#F4E4BC", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        tk.Label(
            main_frame,
            text="Label Name:",
            font=("Times New Roman", 11, "bold"),
            bg="#F4E4BC",
            fg="#3D2817"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.name_entry = tk.Entry(main_frame, font=("Times New Roman", 11), width=30)
        self.name_entry.pack(fill=tk.X, pady=(0, 15))
        self.name_entry.insert(0, initial_name)
        
        # Symbol (emoji)
        tk.Label(
            main_frame,
            text="Symbol (Emoji):",
            font=("Times New Roman", 11, "bold"),
            bg="#F4E4BC",
            fg="#3D2817"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        symbol_frame = tk.Frame(main_frame, bg="#F4E4BC")
        symbol_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.symbol_entry = tk.Entry(symbol_frame, font=("Times New Roman", 16), width=10)
        self.symbol_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.symbol_entry.insert(0, initial_symbol)
        
        # Emoji suggestions
        emoji_suggestions = ["📋", "⚔️", "🛡️", "✨", "🔮", "📜", "🗡️", "🏰", "🌿", "⭐", "💎", "🔥", "❄️", "🌙", "☀️"]
        suggestion_frame = tk.Frame(main_frame, bg="#F4E4BC")
        suggestion_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            suggestion_frame,
            text="Quick select:",
            font=("Times New Roman", 9),
            bg="#F4E4BC",
            fg="#3D2817"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        for emoji in emoji_suggestions:
            btn = tk.Button(
                suggestion_frame,
                text=emoji,
                command=lambda e=emoji: self.symbol_entry.delete(0, tk.END) or self.symbol_entry.insert(0, e),
                font=("Times New Roman", 12),
                bg="#F4E4BC",
                relief=tk.FLAT,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Color
        tk.Label(
            main_frame,
            text="Color (hex code):",
            font=("Times New Roman", 11, "bold"),
            bg="#F4E4BC",
            fg="#3D2817"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        color_frame = tk.Frame(main_frame, bg="#F4E4BC")
        color_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.color_entry = tk.Entry(color_frame, font=("Times New Roman", 11), width=15)
        self.color_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.color_entry.insert(0, initial_color)
        
        # Color suggestions
        color_suggestions = ["#8B7355", "#4A7C59", "#D4AF37", "#8B4513", "#8B0000", "#4B0082", "#006400"]
        for color in color_suggestions:
            btn = tk.Button(
                color_frame,
                text="●",
                fg=color,
                font=("Times New Roman", 16),
                bg="#F4E4BC",
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda c=color: self.color_entry.delete(0, tk.END) or self.color_entry.insert(0, c)
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg="#F4E4BC")
        btn_frame.pack(fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Save",
            command=self.save,
            font=("Times New Roman", 10),
            bg="#4A7C59",
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.dialog.destroy,
            font=("Times New Roman", 10),
            bg="#8B0000",
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=5)
        
        self.dialog.focus_set()
        self.name_entry.focus_set()
        if initial_name:
            self.name_entry.select_range(0, tk.END)
    
    def save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Invalid", "Label name cannot be empty.")
            return
        
        symbol = self.symbol_entry.get().strip() or "📋"
        color = self.color_entry.get().strip() or "#8B7355"
        
        self.result = (name, symbol, color)
        self.dialog.destroy()


def main():
    root = tk.Tk()
    app = TaskTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
