import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from calendar import day_name

class Task:
    def __init__(self, title: str, description: str = "", labels: List[str] = None, 
                 completed: bool = False, task_type: str = "oneshot", 
                 due_date: str = None, days_of_week: List[int] = None, 
                 start_date: str = None, repeat_frequency: int = 1):
        self.title = title
        self.description = description
        self.labels = labels if labels else []
        self.completed = completed
        self.task_type = task_type  # "oneshot" or "weekly"
        self.due_date = due_date  # ISO format date string for oneshot tasks
        self.days_of_week = days_of_week if days_of_week else []  # 0=Monday, 6=Sunday
        self.start_date = start_date  # ISO format date string for weekly tasks
        self.repeat_frequency = repeat_frequency  # Every N weeks
        self.created_at = datetime.now().isoformat()
        self.id = datetime.now().timestamp()
    
    def to_dict(self):
        return {
            'title': self.title,
            'description': self.description,
            'labels': self.labels,
            'completed': self.completed,
            'task_type': self.task_type,
            'due_date': self.due_date,
            'days_of_week': self.days_of_week,
            'start_date': self.start_date,
            'repeat_frequency': self.repeat_frequency,
            'created_at': self.created_at,
            'id': self.id
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        task = cls(
            title=data['title'],
            description=data.get('description', ''),
            labels=data.get('labels', []),
            completed=data.get('completed', False),
            task_type=data.get('task_type', 'oneshot'),
            due_date=data.get('due_date'),
            days_of_week=data.get('days_of_week', []),
            start_date=data.get('start_date'),
            repeat_frequency=data.get('repeat_frequency', 1)
        )
        task.created_at = data.get('created_at', datetime.now().isoformat())
        task.id = data.get('id', datetime.now().timestamp())
        return task
    
    def is_due_on_date(self, target_date: date) -> bool:
        """Check if this task is due on the given date"""
        if self.task_type == "oneshot":
            if not self.due_date:
                return False
            try:
                due = datetime.fromisoformat(self.due_date).date()
                return due == target_date
            except:
                return False
        elif self.task_type == "weekly":
            if not self.start_date or not self.days_of_week:
                return False
            try:
                start = datetime.fromisoformat(self.start_date).date()
                # Check if target_date is on one of the selected days
                day_of_week = target_date.weekday()  # 0=Monday, 6=Sunday
                if day_of_week not in self.days_of_week:
                    return False
                
                # Check if target_date is after start_date
                if target_date < start:
                    return False
                
                # Check if it's the right week frequency
                days_diff = (target_date - start).days
                weeks_diff = days_diff // 7
                return weeks_diff % self.repeat_frequency == 0
            except:
                return False
        return False

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
        self.root.geometry("1200x800")
        
        # Data storage
        self.tasks: List[Task] = []
        self.labels: Dict[str, Label] = {}
        self.filter_label: Optional[str] = None
        self.label_index_map: Dict[int, str] = {}
        
        # Date and view management
        self.current_date = date.today()
        self.view_mode = "day"  # "day" or "week"
        
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
        
        # Crisp rustic color scheme - modern but warm
        self.bg_color = "#F8F6F3"  # Warm off-white background
        self.card_color = "#FFFFFF"  # Clean white cards
        self.text_color = "#3A3A3A"  # Warm dark gray text
        self.text_secondary = "#6B6B6B"  # Muted gray
        self.accent_color = "#8B6F47"  # Warm brown/rustic accent
        self.accent_hover = "#7A5F3A"  # Darker brown
        self.success_color = "#6B8E5A"  # Muted green
        self.danger_color = "#C97D60"  # Warm terracotta red
        self.warning_color = "#D4A574"  # Warm amber
        self.border_color = "#E5DDD5"  # Warm beige border
        self.highlight_color = "#F5EDE0"  # Warm cream highlight
        
        self.root.configure(bg=self.bg_color)
        
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=24, pady=24)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with modern styling
        title_frame = tk.Frame(main_frame, bg=self.bg_color)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(
            title_frame,
            text="📜 Quest Journal",
            font=("Georgia", 26, "bold"),
            bg=self.bg_color,
            fg=self.accent_color
        )
        title_label.pack()
        
        subtitle = tk.Label(
            title_frame,
            text="Organize your tasks and adventures",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.text_secondary
        )
        subtitle.pack(pady=(6, 0))
        
        # Date navigation and view mode
        date_frame = tk.Frame(main_frame, bg=self.bg_color)
        date_frame.pack(fill=tk.X, pady=(0, 16))
        
        # View mode toggle - rustic segmented style
        view_mode_frame = tk.Frame(date_frame, bg=self.bg_color, relief=tk.FLAT, bd=0)
        view_mode_frame.pack(side=tk.LEFT)
        
        tk.Label(
            view_mode_frame,
            text="View:",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.text_secondary
        ).pack(side=tk.LEFT, padx=(0, 10), pady=8)
        
        self.view_mode_var = tk.StringVar(value=self.view_mode)
        day_view_btn = tk.Radiobutton(
            view_mode_frame,
            text="Day",
            variable=self.view_mode_var,
            value="day",
            command=self.toggle_view_mode,
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.text_color,
            selectcolor=self.highlight_color,
            activebackground=self.bg_color,
            activeforeground=self.accent_color,
            indicatoron=0,
            width=8,
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightcolor=self.border_color,
            highlightbackground=self.border_color
        )
        day_view_btn.pack(side=tk.LEFT, padx=2)
        
        week_view_btn = tk.Radiobutton(
            view_mode_frame,
            text="Week",
            variable=self.view_mode_var,
            value="week",
            command=self.toggle_view_mode,
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg=self.text_color,
            selectcolor=self.highlight_color,
            activebackground=self.bg_color,
            activeforeground=self.accent_color,
            indicatoron=0,
            width=8,
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightcolor=self.border_color,
            highlightbackground=self.border_color
        )
        week_view_btn.pack(side=tk.LEFT, padx=2)
        
        # Date navigation (for day view) - modern style
        if self.view_mode == "day":
            nav_frame = tk.Frame(date_frame, bg=self.bg_color)
            nav_frame.pack(side=tk.RIGHT)
            
            prev_btn = tk.Button(
                nav_frame,
                text="◀",
                command=self.previous_day,
                font=("Segoe UI", 12),
                bg=self.card_color,
                fg=self.text_color,
                relief=tk.FLAT,
                bd=1,
                cursor="hand2",
                width=3,
                highlightthickness=1,
                highlightcolor=self.border_color,
                highlightbackground=self.border_color,
                activebackground=self.highlight_color,
                activeforeground=self.text_color
            )
            prev_btn.pack(side=tk.LEFT, padx=2)
            
            self.date_label = tk.Label(
                nav_frame,
                text=self.format_date(self.current_date),
                font=("Georgia", 13, "bold"),
                bg=self.bg_color,
                fg=self.accent_color,
                width=28
            )
            self.date_label.pack(side=tk.LEFT, padx=10)
            
            next_btn = tk.Button(
                nav_frame,
                text="▶",
                command=self.next_day,
                font=("Segoe UI", 12),
                bg=self.card_color,
                fg=self.text_color,
                relief=tk.FLAT,
                bd=1,
                cursor="hand2",
                width=3,
                highlightthickness=1,
                highlightcolor=self.border_color,
                highlightbackground=self.border_color,
                activebackground=self.highlight_color,
                activeforeground=self.text_color
            )
            next_btn.pack(side=tk.LEFT, padx=2)
            
            today_btn = tk.Button(
                nav_frame,
                text="Today",
                command=self.go_to_today,
                font=("Segoe UI", 10),
                bg=self.accent_color,
                fg="white",
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                padx=14,
                pady=7,
                activebackground=self.accent_hover,
                activeforeground="white"
            )
            today_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Content area with two columns
        content_frame = tk.Frame(main_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Labels - modern card style
        left_panel = tk.Frame(content_frame, bg=self.card_color, relief=tk.FLAT, bd=0)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 12), expand=False)
        left_panel.config(width=260)
        
        # Add subtle shadow effect with border
        label_title_frame = tk.Frame(left_panel, bg=self.border_color, height=1)
        label_title_frame.pack(fill=tk.X)
        
        label_title = tk.Label(
            left_panel,
            text="Labels",
            font=("Georgia", 14, "bold"),
            bg=self.card_color,
            fg=self.accent_color
        )
        label_title.pack(pady=(18, 14), padx=18, anchor=tk.W)
        
        # Label list with scrollbar - modern style
        label_list_frame = tk.Frame(left_panel, bg=self.card_color)
        label_list_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        
        self.label_listbox = tk.Listbox(
            label_list_frame,
            font=("Segoe UI", 10),
            bg=self.card_color,
            fg=self.text_color,
            selectbackground=self.accent_color,
            selectforeground="white",
            relief=tk.FLAT,
            bd=1,
            highlightthickness=1,
            highlightcolor=self.border_color,
            highlightbackground=self.border_color
        )
        self.label_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        label_scrollbar = tk.Scrollbar(label_list_frame, orient=tk.VERTICAL, command=self.label_listbox.yview)
        label_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.label_listbox.config(yscrollcommand=label_scrollbar.set)
        
        # Store mapping of listbox index to label name for easier lookup
        self.label_index_map = {}
        
        # Label buttons - modern flat style
        label_btn_frame = tk.Frame(left_panel, bg=self.card_color)
        label_btn_frame.pack(fill=tk.X, pady=(0, 16), padx=16)
        
        def create_modern_button(parent, text, command, bg_color, fg_color="white", is_primary=False):
            btn = tk.Button(
                parent,
                text=text,
                command=command,
                font=("Segoe UI", 10),
                bg=bg_color,
                fg=fg_color,
                relief=tk.FLAT,
                bd=0,
                cursor="hand2",
                pady=8,
                activebackground=bg_color if not is_primary else self.accent_hover,
                activeforeground=fg_color
            )
            if is_primary:
                btn.config(relief=tk.FLAT, bd=0)
            return btn
        
        add_label_btn = tk.Button(
            label_btn_frame,
            text="➕ Add Label",
            command=self.add_label,
            font=("Segoe UI", 10),
            bg=self.accent_color,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=9,
            activebackground=self.accent_hover,
            activeforeground="white"
        )
        add_label_btn.pack(fill=tk.X, pady=(0, 7))
        
        edit_label_btn = tk.Button(
            label_btn_frame,
            text="✏️ Edit",
            command=self.edit_label,
            font=("Segoe UI", 10),
            bg=self.card_color,
            fg=self.text_color,
            relief=tk.FLAT,
            bd=1,
            cursor="hand2",
            pady=8,
            highlightthickness=1,
            highlightcolor=self.border_color,
            highlightbackground=self.border_color,
            activebackground=self.highlight_color,
            activeforeground=self.text_color
        )
        edit_label_btn.pack(fill=tk.X, pady=(0, 7))
        
        delete_label_btn = tk.Button(
            label_btn_frame,
            text="🗑️ Delete",
            command=self.delete_label,
            font=("Segoe UI", 10),
            bg=self.danger_color,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=9,
            activebackground="#B86A4F",
            activeforeground="white"
        )
        delete_label_btn.pack(fill=tk.X, pady=(0, 7))
        
        filter_btn = tk.Button(
            label_btn_frame,
            text="🔍 Filter",
            command=self.filter_by_label,
            font=("Segoe UI", 10),
            bg=self.card_color,
            fg=self.text_color,
            relief=tk.FLAT,
            bd=1,
            cursor="hand2",
            pady=8,
            highlightthickness=1,
            highlightcolor=self.border_color,
            highlightbackground=self.border_color,
            activebackground=self.highlight_color,
            activeforeground=self.text_color
        )
        filter_btn.pack(fill=tk.X, pady=(0, 7))
        
        clear_filter_btn = tk.Button(
            label_btn_frame,
            text="🌐 Show All",
            command=self.clear_filter,
            font=("Segoe UI", 10),
            bg=self.card_color,
            fg=self.text_color,
            relief=tk.FLAT,
            bd=1,
            cursor="hand2",
            pady=8,
            highlightthickness=1,
            highlightcolor=self.border_color,
            highlightbackground=self.border_color,
            activebackground=self.highlight_color,
            activeforeground=self.text_color
        )
        clear_filter_btn.pack(fill=tk.X)
        
        # Right panel - Tasks - modern card style
        right_panel = tk.Frame(content_frame, bg=self.card_color, relief=tk.FLAT, bd=0)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        task_title_frame = tk.Frame(right_panel, bg=self.card_color)
        task_title_frame.pack(fill=tk.X, pady=(16, 12), padx=16)
        
        if self.view_mode == "week":
            task_title = tk.Label(
                task_title_frame,
                text="Weekly Overview",
                font=("Georgia", 14, "bold"),
                bg=self.card_color,
                fg=self.accent_color
            )
            task_title.pack(side=tk.LEFT)
        else:
            task_title = tk.Label(
                task_title_frame,
                text="Tasks",
                font=("Georgia", 14, "bold"),
                bg=self.card_color,
                fg=self.accent_color
            )
            task_title.pack(side=tk.LEFT)
        
        if self.filter_label:
            filter_indicator = tk.Label(
                task_title_frame,
                text=f"Filtered: {self.labels[self.filter_label].symbol} {self.filter_label}",
                font=("Segoe UI", 9),
                bg=self.card_color,
                fg=self.text_secondary
            )
            filter_indicator.pack(side=tk.RIGHT)
        
        # Task display area
        if self.view_mode == "week":
            self.setup_week_view(right_panel)
        else:
            self.setup_day_view(right_panel)
    
    def setup_day_view(self, parent):
        # Task list with scrollbar - modern style
        task_list_frame = tk.Frame(parent, bg=self.card_color)
        task_list_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        
        self.task_listbox = tk.Listbox(
            task_list_frame,
            font=("Segoe UI", 10),
            bg=self.card_color,
            fg=self.text_color,
            selectbackground=self.accent_color,
            selectforeground="white",
            relief=tk.FLAT,
            bd=1,
            height=15,
            highlightthickness=1,
            highlightcolor=self.border_color,
            highlightbackground=self.border_color
        )
        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        task_scrollbar = tk.Scrollbar(task_list_frame, orient=tk.VERTICAL, command=self.task_listbox.yview)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_listbox.config(yscrollcommand=task_scrollbar.set)
        
        # Task buttons - modern style
        task_btn_frame = tk.Frame(parent, bg=self.card_color)
        task_btn_frame.pack(fill=tk.X, pady=(0, 16), padx=16)
        
        add_task_btn = tk.Button(
            task_btn_frame,
            text="➕ New Task",
            command=self.add_task,
            font=("Segoe UI", 10),
            bg=self.accent_color,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=10,
            activebackground=self.accent_hover,
            activeforeground="white"
        )
        add_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        
        edit_task_btn = tk.Button(
            task_btn_frame,
            text="✏️ Edit",
            command=self.edit_task,
            font=("Segoe UI", 10),
            bg=self.card_color,
            fg=self.text_color,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=10,
            activebackground=self.border_color,
            activeforeground=self.text_color
        )
        edit_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
        
        complete_task_btn = tk.Button(
            task_btn_frame,
            text="✅ Complete",
            command=self.toggle_complete,
            font=("Segoe UI", 10),
            bg=self.success_color,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=10,
            activebackground="#38A169",
            activeforeground="white"
        )
        complete_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
        
        delete_task_btn = tk.Button(
            task_btn_frame,
            text="🗑️ Delete",
            command=self.delete_task,
            font=("Segoe UI", 10),
            bg=self.danger_color,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=10,
            activebackground="#E53E3E",
            activeforeground="white"
        )
        delete_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))
    
    def setup_week_view(self, parent):
        # Calculate week start (Monday)
        week_start = self.current_date - timedelta(days=self.current_date.weekday())
        week_days = [week_start + timedelta(days=i) for i in range(7)]
        
        # Create scrollable canvas for week view - modern style
        week_canvas_frame = tk.Frame(parent, bg=self.card_color)
        week_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        
        week_canvas = tk.Canvas(week_canvas_frame, bg=self.card_color, highlightthickness=0)
        week_scrollbar = tk.Scrollbar(week_canvas_frame, orient=tk.VERTICAL, command=week_canvas.yview)
        week_content = tk.Frame(week_canvas, bg=self.card_color)
        
        week_content.bind(
            "<Configure>",
            lambda e: week_canvas.configure(scrollregion=week_canvas.bbox("all"))
        )
        
        week_canvas.create_window((0, 0), window=week_content, anchor="nw")
        week_canvas.configure(yscrollcommand=week_scrollbar.set)
        
        # Create day columns
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_emojis = ["🌅", "🌄", "🌆", "🌇", "🌃", "🌙", "☀️"]
        
        self.week_task_frames = {}
        
        for i, (day_date, day_name_full) in enumerate(zip(week_days, day_names)):
            day_frame = tk.Frame(week_content, bg=self.bg_color, relief=tk.FLAT, bd=0)
            day_frame.grid(row=0, column=i, padx=4, pady=4, sticky="nsew")
            week_content.grid_columnconfigure(i, weight=1)
            
            # Day header - rustic style
            day_header = tk.Frame(day_frame, bg=self.accent_color)
            day_header.pack(fill=tk.X)
            
            day_label = tk.Label(
                day_header,
                text=f"{day_name_full[:3]}\n{day_date.strftime('%m/%d')}",
                font=("Georgia", 10, "bold"),
                bg=self.accent_color,
                fg="white"
            )
            day_label.pack(pady=9)
            
            # Tasks for this day - modern card style
            day_tasks_frame = tk.Frame(day_frame, bg=self.bg_color)
            day_tasks_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
            
            tasks_for_day = self.get_tasks_for_date(day_date)
            self.week_task_frames[day_date] = day_tasks_frame
            
            if not tasks_for_day:
                no_tasks = tk.Label(
                    day_tasks_frame,
                    text="No tasks",
                    font=("Segoe UI", 9),
                    bg=self.bg_color,
                    fg=self.text_secondary
                )
                no_tasks.pack(pady=12)
            else:
                for task in tasks_for_day:
                    task_frame = tk.Frame(day_tasks_frame, bg=self.card_color, relief=tk.FLAT, bd=0)
                    task_frame.pack(fill=tk.X, pady=3, padx=2)
                    
                    label_str = " ".join([self.labels[label].symbol for label in task.labels if label in self.labels])
                    status = "✅" if task.completed else "⭕"
                    task_type_icon = "🔄" if task.task_type == "weekly" else "📌"
                    
                    task_text = f"{status} {task_type_icon} {label_str} {task.title}"
                    if len(task_text) > 40:
                        task_text = task_text[:37] + "..."
                    
                    task_label = tk.Label(
                        task_frame,
                        text=task_text,
                        font=("Segoe UI", 9),
                        bg=self.card_color,
                        fg=self.text_color if not task.completed else self.text_secondary,
                        wraplength=120,
                        justify=tk.LEFT
                    )
                    task_label.pack(anchor=tk.W, padx=8, pady=6)
        
        week_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        week_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Task buttons - rustic style
        task_btn_frame = tk.Frame(parent, bg=self.card_color)
        task_btn_frame.pack(fill=tk.X, pady=(0, 16), padx=16)
        
        add_task_btn = tk.Button(
            task_btn_frame,
            text="➕ New Task",
            command=self.add_task,
            font=("Segoe UI", 10),
            bg=self.accent_color,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=10,
            activebackground=self.accent_hover,
            activeforeground="white"
        )
        add_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        
        edit_task_btn = tk.Button(
            task_btn_frame,
            text="✏️ Edit",
            command=self.edit_task,
            font=("Segoe UI", 10),
            bg=self.card_color,
            fg=self.text_color,
            relief=tk.FLAT,
            bd=1,
            cursor="hand2",
            pady=10,
            highlightthickness=1,
            highlightcolor=self.border_color,
            highlightbackground=self.border_color,
            activebackground=self.highlight_color,
            activeforeground=self.text_color
        )
        edit_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
        
        complete_task_btn = tk.Button(
            task_btn_frame,
            text="✅ Complete",
            command=self.toggle_complete,
            font=("Segoe UI", 10),
            bg=self.success_color,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=10,
            activebackground="#5A7A4A",
            activeforeground="white"
        )
        complete_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)
        
        delete_task_btn = tk.Button(
            task_btn_frame,
            text="🗑️ Delete",
            command=self.delete_task,
            font=("Segoe UI", 10),
            bg=self.danger_color,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            pady=10,
            activebackground="#B86A4F",
            activeforeground="white"
        )
        delete_task_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))
    
    def format_date(self, d: date) -> str:
        """Format date for display"""
        return d.strftime("%A, %B %d, %Y")
    
    def previous_day(self):
        self.current_date -= timedelta(days=1)
        if hasattr(self, 'date_label'):
            self.date_label.config(text=self.format_date(self.current_date))
        self.update_task_list()
    
    def next_day(self):
        self.current_date += timedelta(days=1)
        if hasattr(self, 'date_label'):
            self.date_label.config(text=self.format_date(self.current_date))
        self.update_task_list()
    
    def go_to_today(self):
        self.current_date = date.today()
        if hasattr(self, 'date_label'):
            self.date_label.config(text=self.format_date(self.current_date))
        self.update_task_list()
    
    def toggle_view_mode(self):
        self.view_mode = self.view_mode_var.get()
        self.setup_ui()
        self.update_task_list()
    
    def get_tasks_for_date(self, target_date: date) -> List[Task]:
        """Get all tasks that are due on the given date"""
        tasks = []
        for task in self.tasks:
            if self.filter_label and self.filter_label not in task.labels:
                continue
            if task.is_due_on_date(target_date):
                tasks.append(task)
        return tasks
    
    def add_task(self):
        dialog = TaskDialog(self.root, "Add New Quest", labels=list(self.labels.keys()))
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            task_data = dialog.result
            task = Task(
                title=task_data['title'],
                description=task_data['description'],
                labels=task_data['labels'],
                task_type=task_data['task_type'],
                due_date=task_data.get('due_date'),
                days_of_week=task_data.get('days_of_week'),
                start_date=task_data.get('start_date'),
                repeat_frequency=task_data.get('repeat_frequency', 1)
            )
            self.tasks.append(task)
            self.update_task_list()
            self.save_data()
    
    def edit_task(self):
        if self.view_mode == "day":
            selection = self.task_listbox.curselection()
            if not selection:
                messagebox.showinfo("No Selection", "Please select a quest to edit.")
                return
            
            task = self.get_selected_task()
        else:
            # In week view, need to select from a day
            messagebox.showinfo("Edit Quest", "Please switch to Day view to edit quests, or select a quest from the day view.")
            return
        
        if not task:
            return
        
        dialog = TaskDialog(
            self.root,
            "Edit Quest",
            labels=list(self.labels.keys()),
            initial_data={
                'title': task.title,
                'description': task.description,
                'labels': task.labels,
                'task_type': task.task_type,
                'due_date': task.due_date,
                'days_of_week': task.days_of_week,
                'start_date': task.start_date,
                'repeat_frequency': task.repeat_frequency
            }
        )
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            task_data = dialog.result
            task.title = task_data['title']
            task.description = task_data['description']
            task.labels = task_data['labels']
            task.task_type = task_data['task_type']
            task.due_date = task_data.get('due_date')
            task.days_of_week = task_data.get('days_of_week')
            task.start_date = task_data.get('start_date')
            task.repeat_frequency = task_data.get('repeat_frequency', 1)
            self.update_task_list()
            self.save_data()
    
    def delete_task(self):
        if self.view_mode == "day":
            selection = self.task_listbox.curselection()
            if not selection:
                messagebox.showinfo("No Selection", "Please select a quest to delete.")
                return
            
            task = self.get_selected_task()
        else:
            messagebox.showinfo("Delete Quest", "Please switch to Day view to delete quests.")
            return
        
        if not task:
            return
        
        if messagebox.askyesno("Confirm", f"Remove quest '{task.title}' from the journal?"):
            self.tasks.remove(task)
            self.update_task_list()
            self.save_data()
    
    def toggle_complete(self):
        if self.view_mode == "day":
            selection = self.task_listbox.curselection()
            if not selection:
                messagebox.showinfo("No Selection", "Please select a quest to mark.")
                return
            
            task = self.get_selected_task()
        else:
            messagebox.showinfo("Complete Quest", "Please switch to Day view to mark quests complete.")
            return
        
        if not task:
            return
        
        task.completed = not task.completed
        self.update_task_list()
        self.save_data()
    
    def get_selected_task(self) -> Optional[Task]:
        if self.view_mode != "day" or not hasattr(self, 'task_listbox'):
            return None
        
        selection = self.task_listbox.curselection()
        if not selection:
            return None
        
        index = selection[0]
        filtered_tasks = self.get_filtered_tasks()
        if 0 <= index < len(filtered_tasks):
            return filtered_tasks[index]
        return None
    
    def get_filtered_tasks(self) -> List[Task]:
        if self.view_mode == "day":
            return self.get_tasks_for_date(self.current_date)
        else:
            return [t for t in self.tasks if self.filter_label is None or self.filter_label in t.labels]
    
    def update_task_list(self):
        if self.view_mode == "week":
            # Rebuild week view to refresh tasks - simpler approach
            self.setup_ui()
            return
        
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
            task_type_icon = "🔄" if task.task_type == "weekly" else "📌"
            display = f"{status} {task_type_icon} {label_str}{task.title}"
            
            # Add date info
            if task.task_type == "oneshot" and task.due_date:
                try:
                    due = datetime.fromisoformat(task.due_date).date()
                    display += f" (Due: {due.strftime('%m/%d')})"
                except:
                    pass
            elif task.task_type == "weekly":
                days = [day_name[d] for d in task.days_of_week]
                display += f" (Weekly: {', '.join([d[:3] for d in days])})"
            
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
    def __init__(self, parent, title, labels=None, initial_data=None):
        self.result = None
        initial_data = initial_data or {}
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x650")
        self.dialog.configure(bg="#F5F7FA")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (650 // 2)
        self.dialog.geometry(f"600x650+{x}+{y}")
        
        main_frame = tk.Frame(self.dialog, bg="#FFFFFF", padx=24, pady=24)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        tk.Label(
            main_frame,
            text="Title",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#2D3748"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        self.title_entry = tk.Entry(main_frame, font=("Segoe UI", 11), width=50, relief=tk.FLAT, bd=0, highlightthickness=1, highlightcolor="#4299E1", highlightbackground="#E2E8F0")
        self.title_entry.pack(fill=tk.X, pady=(0, 20), ipady=8)
        self.title_entry.insert(0, initial_data.get('title', ''))
        
        # Description
        tk.Label(
            main_frame,
            text="Description",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#2D3748"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        desc_frame = tk.Frame(main_frame, bg="#FFFFFF")
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        self.desc_text = tk.Text(desc_frame, font=("Segoe UI", 11), width=50, height=6, relief=tk.FLAT, bd=0, highlightthickness=1, highlightcolor="#4299E1", highlightbackground="#E2E8F0", wrap=tk.WORD)
        self.desc_text.pack(fill=tk.BOTH, expand=True)
        self.desc_text.insert("1.0", initial_data.get('description', ''))
        
        # Task Type
        tk.Label(
            main_frame,
            text="Task Type",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#2D3748"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        type_frame = tk.Frame(main_frame, bg="#FFFFFF")
        type_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.task_type_var = tk.StringVar(value=initial_data.get('task_type', 'oneshot'))
        
        oneshot_radio = tk.Radiobutton(
            type_frame,
            text="📌 One-Shot Task",
            variable=self.task_type_var,
            value="oneshot",
            command=self.update_task_type_fields,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#2D3748",
            selectcolor="#4299E1",
            activebackground="#FFFFFF",
            activeforeground="#2D3748"
        )
        oneshot_radio.pack(side=tk.LEFT, padx=(0, 16))
        
        weekly_radio = tk.Radiobutton(
            type_frame,
            text="🔄 Weekly Task",
            variable=self.task_type_var,
            value="weekly",
            command=self.update_task_type_fields,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#2D3748",
            selectcolor="#4299E1",
            activebackground="#FFFFFF",
            activeforeground="#2D3748"
        )
        weekly_radio.pack(side=tk.LEFT)
        
        # Date fields container
        self.date_fields_frame = tk.Frame(main_frame, bg="#FFFFFF")
        self.date_fields_frame.pack(fill=tk.X, pady=(0, 20))
        
        # One-shot date field
        self.oneshot_date_frame = tk.Frame(self.date_fields_frame, bg="#FFFFFF")
        
        tk.Label(
            self.oneshot_date_frame,
            text="Due Date (YYYY-MM-DD)",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#2D3748"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        self.due_date_entry = tk.Entry(self.oneshot_date_frame, font=("Segoe UI", 10), width=20, relief=tk.FLAT, bd=0, highlightthickness=1, highlightcolor="#4299E1", highlightbackground="#E2E8F0")
        self.due_date_entry.pack(anchor=tk.W, ipady=6)
        if initial_data.get('due_date'):
            try:
                due = datetime.fromisoformat(initial_data['due_date']).date()
                self.due_date_entry.insert(0, due.isoformat())
            except:
                pass
        
        # Weekly task fields
        self.weekly_fields_frame = tk.Frame(self.date_fields_frame, bg="#FFFFFF")
        
        # Start date
        tk.Label(
            self.weekly_fields_frame,
            text="Start Date (YYYY-MM-DD)",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#2D3748"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        self.start_date_entry = tk.Entry(self.weekly_fields_frame, font=("Segoe UI", 10), width=20, relief=tk.FLAT, bd=0, highlightthickness=1, highlightcolor="#4299E1", highlightbackground="#E2E8F0")
        self.start_date_entry.pack(anchor=tk.W, pady=(0, 12), ipady=6)
        if initial_data.get('start_date'):
            try:
                start = datetime.fromisoformat(initial_data['start_date']).date()
                self.start_date_entry.insert(0, start.isoformat())
            except:
                pass
        
        # Days of week
        tk.Label(
            self.weekly_fields_frame,
            text="Days of Week",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#2D3748"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        days_frame = tk.Frame(self.weekly_fields_frame, bg="#FFFFFF")
        days_frame.pack(anchor=tk.W, pady=(0, 12))
        
        self.days_vars = {}
        day_names_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day_name in enumerate(day_names_short):
            var = tk.BooleanVar()
            var.set(i in (initial_data.get('days_of_week', [])))
            self.days_vars[i] = var
            
            check = tk.Checkbutton(
                days_frame,
                text=day_name,
                variable=var,
                font=("Segoe UI", 9),
                bg="#FFFFFF",
                fg="#2D3748",
                selectcolor="#4299E1",
                activebackground="#FFFFFF",
                activeforeground="#2D3748"
            )
            check.pack(side=tk.LEFT, padx=6)
        
        # Repeat frequency
        tk.Label(
            self.weekly_fields_frame,
            text="Repeat Every N Weeks",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#2D3748"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        freq_frame = tk.Frame(self.weekly_fields_frame, bg="#FFFFFF")
        freq_frame.pack(anchor=tk.W)
        
        self.repeat_freq_var = tk.StringVar(value=str(initial_data.get('repeat_frequency', 1)))
        freq_spinbox = tk.Spinbox(
            freq_frame,
            from_=1,
            to=52,
            textvariable=self.repeat_freq_var,
            font=("Segoe UI", 10),
            width=5,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightcolor="#4299E1",
            highlightbackground="#E2E8F0"
        )
        freq_spinbox.pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Label(
            freq_frame,
            text="weeks",
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#718096"
        ).pack(side=tk.LEFT)
        
        # Update fields based on initial type
        self.update_task_type_fields()
        
        # Labels
        tk.Label(
            main_frame,
            text="Labels",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#2D3748"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        label_frame = tk.Frame(main_frame, bg="#FFFFFF")
        label_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        if not labels:
            no_labels = tk.Label(
                label_frame,
                text="No labels available. Create labels first!",
                font=("Segoe UI", 9),
                bg="#FFFFFF",
                fg="#718096"
            )
            no_labels.pack(anchor=tk.W, pady=5)
        
        self.label_vars = {}
        if labels:
            # Create a scrollable frame for labels
            label_canvas = tk.Canvas(label_frame, bg="#FFFFFF", highlightthickness=0, height=80)
            label_scrollbar = tk.Scrollbar(label_frame, orient=tk.VERTICAL, command=label_canvas.yview)
            label_scrollable_frame = tk.Frame(label_canvas, bg="#FFFFFF")
            
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
                var.set(label_name in (initial_data.get('labels', [])))
                self.label_vars[label_name] = var
                
                check = tk.Checkbutton(
                    label_scrollable_frame,
                    text=label_name,
                    variable=var,
                    font=("Segoe UI", 10),
                    bg="#FFFFFF",
                    fg="#2D3748",
                    selectcolor="#4299E1",
                    activebackground="#FFFFFF",
                    activeforeground="#2D3748"
                )
                check.pack(anchor=tk.W, pady=3)
            
            label_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            label_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons - modern style
        btn_frame = tk.Frame(main_frame, bg="#FFFFFF")
        btn_frame.pack(fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Save",
            command=self.save,
            font=("Segoe UI", 10, "bold"),
            bg="#4299E1",
            fg="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=24,
            pady=10,
            activebackground="#3182CE",
            activeforeground="white"
        ).pack(side=tk.RIGHT, padx=(8, 0))
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.dialog.destroy,
            font=("Segoe UI", 10),
            bg="#E2E8F0",
            fg="#2D3748",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=24,
            pady=10,
            activebackground="#CBD5E0",
            activeforeground="#2D3748"
        ).pack(side=tk.RIGHT)
        
        self.dialog.focus_set()
        self.title_entry.focus_set()
        self.title_entry.select_range(0, tk.END)
    
    def update_task_type_fields(self):
        task_type = self.task_type_var.get()
        # Clear all
        for widget in self.date_fields_frame.winfo_children():
            widget.pack_forget()
        
        if task_type == "oneshot":
            self.oneshot_date_frame.pack(fill=tk.X, anchor=tk.W)
        else:
            self.weekly_fields_frame.pack(fill=tk.X, anchor=tk.W)
    
    def save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Invalid", "Quest title cannot be empty.")
            return
        
        description = self.desc_text.get("1.0", tk.END).strip()
        selected_labels = [name for name, var in self.label_vars.items() if var.get()]
        task_type = self.task_type_var.get()
        
        result = {
            'title': title,
            'description': description,
            'labels': selected_labels,
            'task_type': task_type
        }
        
        if task_type == "oneshot":
            due_date_str = self.due_date_entry.get().strip()
            if due_date_str:
                try:
                    # Validate date format
                    datetime.strptime(due_date_str, "%Y-%m-%d")
                    result['due_date'] = due_date_str
                except ValueError:
                    messagebox.showerror("Invalid Date", "Due date must be in YYYY-MM-DD format.")
                    return
        else:  # weekly
            start_date_str = self.start_date_entry.get().strip()
            if not start_date_str:
                messagebox.showerror("Invalid", "Start date is required for weekly tasks.")
                return
            
            try:
                datetime.strptime(start_date_str, "%Y-%m-%d")
                result['start_date'] = start_date_str
            except ValueError:
                messagebox.showerror("Invalid Date", "Start date must be in YYYY-MM-DD format.")
                return
            
            selected_days = [day for day, var in self.days_vars.items() if var.get()]
            if not selected_days:
                messagebox.showerror("Invalid", "Please select at least one day of the week.")
                return
            
            result['days_of_week'] = selected_days
            result['repeat_frequency'] = int(self.repeat_freq_var.get())
        
        self.result = result
        self.dialog.destroy()


class LabelDialog:
    def __init__(self, parent, title, initial_name="", initial_symbol="📋", initial_color="#8B7355"):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x450")
        self.dialog.configure(bg="#F5F7FA")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (450 // 2)
        self.dialog.geometry(f"400x450+{x}+{y}")
        
        main_frame = tk.Frame(self.dialog, bg="#FFFFFF", padx=24, pady=24)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        tk.Label(
            main_frame,
            text="Label Name",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#2D3748"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        self.name_entry = tk.Entry(main_frame, font=("Segoe UI", 11), width=30, relief=tk.FLAT, bd=0, highlightthickness=1, highlightcolor="#4299E1", highlightbackground="#E2E8F0")
        self.name_entry.pack(fill=tk.X, pady=(0, 20), ipady=8)
        self.name_entry.insert(0, initial_name)
        
        # Symbol (emoji)
        tk.Label(
            main_frame,
            text="Symbol (Emoji)",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#2D3748"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        symbol_frame = tk.Frame(main_frame, bg="#FFFFFF")
        symbol_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.symbol_entry = tk.Entry(symbol_frame, font=("Segoe UI", 18), width=8, relief=tk.FLAT, bd=0, highlightthickness=1, highlightcolor="#4299E1", highlightbackground="#E2E8F0")
        self.symbol_entry.pack(side=tk.LEFT, padx=(0, 12), ipady=4)
        self.symbol_entry.insert(0, initial_symbol)
        
        # Emoji suggestions - expanded list
        emoji_suggestions = [
            "📋", "⚔️", "🛡️", "✨", "🔮", "📜", "🗡️", "🏰", "🌿", "⭐", "💎", "🔥", "❄️", "🌙", "☀️",
            "🗺️", "🧙", "🧝", "🐉", "🦄", "🌳", "🍄", "🌺", "🦋", "🦅", "🐺", "🦌", "🌊", "⛰️", "🌌",
            "🎯", "🏹", "⚡", "🌟", "💫", "🌠", "🎨", "🎭", "🎪", "🎬", "📸", "🎮", "🎲", "🃏", "🎴"
        ]
        suggestion_frame = tk.Frame(main_frame, bg="#FFFFFF")
        suggestion_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            suggestion_frame,
            text="Quick select:",
            font=("Segoe UI", 9),
            bg="#FFFFFF",
            fg="#718096"
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        # Create scrollable emoji buttons
        emoji_canvas = tk.Canvas(suggestion_frame, bg="#FFFFFF", height=44, highlightthickness=0)
        emoji_scroll = tk.Scrollbar(suggestion_frame, orient=tk.HORIZONTAL, command=emoji_canvas.xview)
        emoji_inner = tk.Frame(emoji_canvas, bg="#FFFFFF")
        
        emoji_inner.bind(
            "<Configure>",
            lambda e: emoji_canvas.configure(scrollregion=emoji_canvas.bbox("all"))
        )
        
        emoji_canvas.create_window((0, 0), window=emoji_inner, anchor="nw")
        emoji_canvas.configure(xscrollcommand=emoji_scroll.set)
        
        for emoji in emoji_suggestions:
            btn = tk.Button(
                emoji_inner,
                text=emoji,
                command=lambda e=emoji: self.symbol_entry.delete(0, tk.END) or self.symbol_entry.insert(0, e),
                font=("Segoe UI", 14),
                bg="#FFFFFF",
                relief=tk.FLAT,
                cursor="hand2",
                activebackground="#F7FAFC",
                bd=0
            )
            btn.pack(side=tk.LEFT, padx=3)
        
        emoji_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        emoji_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Color
        tk.Label(
            main_frame,
            text="Color (hex code)",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg="#2D3748"
        ).pack(anchor=tk.W, pady=(0, 8))
        
        color_frame = tk.Frame(main_frame, bg="#FFFFFF")
        color_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.color_entry = tk.Entry(color_frame, font=("Segoe UI", 11), width=15, relief=tk.FLAT, bd=0, highlightthickness=1, highlightcolor="#4299E1", highlightbackground="#E2E8F0")
        self.color_entry.pack(side=tk.LEFT, padx=(0, 12), ipady=6)
        self.color_entry.insert(0, initial_color)
        
        # Color suggestions - modern style
        color_suggestions = ["#4299E1", "#48BB78", "#ED8936", "#F56565", "#9F7AEA", "#38B2AC", "#805AD5"]
        for color in color_suggestions:
            btn = tk.Button(
                color_frame,
                text="●",
                fg=color,
                font=("Segoe UI", 18),
                bg="#FFFFFF",
                relief=tk.FLAT,
                cursor="hand2",
                bd=0,
                activebackground="#F7FAFC",
                command=lambda c=color: self.color_entry.delete(0, tk.END) or self.color_entry.insert(0, c)
            )
            btn.pack(side=tk.LEFT, padx=4)
        
        # Buttons - modern style
        btn_frame = tk.Frame(main_frame, bg="#FFFFFF")
        btn_frame.pack(fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Save",
            command=self.save,
            font=("Segoe UI", 10, "bold"),
            bg="#4299E1",
            fg="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=24,
            pady=10,
            activebackground="#3182CE",
            activeforeground="white"
        ).pack(side=tk.RIGHT, padx=(8, 0))
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.dialog.destroy,
            font=("Segoe UI", 10),
            bg="#E2E8F0",
            fg="#2D3748",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            padx=24,
            pady=10,
            activebackground="#CBD5E0",
            activeforeground="#2D3748"
        ).pack(side=tk.RIGHT)
        
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
