import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import calendar
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class Task:
    def __init__(
        self,
        title: str,
        description: str = "",
        labels: List[str] = None,
        section: str = "Daily",
        importance: int = 5,
        approximate_hours: float = 0.0,
        completed: bool = False,
        proof_text: str = "",
        proof_image: str = "",
        proof_mode: str = "text",
        proof_status: str = "unreviewed",
        proof_feedback: str = "",
    ):
        self.title = title
        self.description = description
        self.labels = labels if labels else []
        self.section = section or "Daily"
        self.importance = max(1, min(int(importance), 10))
        try:
            self.approximate_hours = max(0.0, float(approximate_hours))
        except (TypeError, ValueError):
            self.approximate_hours = 0.0
        self.completed = completed
        self.proof_text = proof_text
        self.proof_image = proof_image
        self.proof_mode = proof_mode if proof_mode in ("text", "image") else "text"
        self.proof_status = proof_status
        self.proof_feedback = proof_feedback
        self.created_at = datetime.now().isoformat()
        self.id = datetime.now().timestamp()
    
    def to_dict(self):
        return {
            'title': self.title,
            'description': self.description,
            'labels': self.labels,
            'section': self.section,
            'importance': self.importance,
            'approximate_hours': self.approximate_hours,
            'completed': self.completed,
            'proof_text': self.proof_text,
            'proof_image': self.proof_image,
            'proof_mode': self.proof_mode,
            'proof_status': self.proof_status,
            'proof_feedback': self.proof_feedback,
            'created_at': self.created_at,
            'id': self.id
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        task = cls(
            title=data['title'],
            description=data.get('description', ''),
            labels=data.get('labels', []),
            section=data.get('section', 'Daily'),
            importance=data.get('importance', 5),
            approximate_hours=data.get('approximate_hours', 0.0),
            completed=data.get('completed', False),
            proof_text=data.get('proof_text', ''),
            proof_image=data.get('proof_image', ''),
            proof_mode=data.get('proof_mode', 'text'),
            proof_status=data.get('proof_status', 'unreviewed'),
            proof_feedback=data.get('proof_feedback', ''),
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
        self.sections: List[str] = ["Daily", "Weekly", "Monthly"]
        self.display_task_map: Dict[int, Optional[Task]] = {}
        self.today = datetime.now().date()
        self.calendar_year = self.today.year
        self.calendar_month = self.today.month
        self.selected_date = self.today
        self.calendar_parent: Optional[tk.Frame] = None
        self.scheduled_plan: Dict[str, List[dict]] = {}
        self.questline_parent: Optional[tk.Frame] = None
        self.questline_task_map: Dict[int, Task] = {}
        self.questline_sidebar_frame: Optional[tk.Frame] = None
        self.questline_selected_task: Optional[Task] = None
        
        # Load data
        self.load_data()
        
        # Setup UI
        self.setup_ui()
        self.update_task_list()
        self.update_label_list()

    def build_questline_tab(self, parent: tk.Frame):
        """Build the Questline tab showing today's scheduled tasks as a treasure map."""
        self.questline_parent = parent

        for widget in parent.winfo_children():
            widget.destroy()

        frame = tk.Frame(parent, bg=self.bg_color, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            frame,
            text="Today's Questline",
            font=("Times New Roman", 18, "bold"),
            bg=self.bg_color,
            fg=self.gold_color,
        )
        title.pack(pady=(0, 5))

        today_label = tk.Label(
            frame,
            text=f"{self.today.strftime('%A, %B %d, %Y')}",
            font=("Times New Roman", 12, "italic"),
            bg=self.bg_color,
            fg=self.paper_color,
        )
        today_label.pack(pady=(0, 10))

        inner = tk.Frame(frame, bg=self.paper_color, relief=tk.RAISED, bd=3)
        inner.pack(fill=tk.BOTH, expand=True)

        # Left: treasure map, Right: quest details sidebar
        map_frame = tk.Frame(inner, bg=self.paper_color)
        map_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5), pady=10)

        sidebar_frame = tk.Frame(inner, bg=self.paper_color, width=260)
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 10), pady=10)
        self.questline_sidebar_frame = sidebar_frame

        canvas_frame = tk.Frame(map_frame, bg=self.paper_color)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.questline_canvas = tk.Canvas(
            canvas_frame,
            bg=self.paper_color,
            highlightthickness=0,
        )
        self.questline_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.questline_canvas.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.questline_canvas.config(yscrollcommand=scroll.set)

        self.questline_task_map = {}
        date_key = self.today.isoformat()
        entries = list(self.scheduled_plan.get(date_key, []))

        if not entries:
            self.questline_canvas.create_text(
                10,
                10,
                anchor="nw",
                text="No quests scheduled for today.\nCreate a questline from the Calendar tab to see your treasure map.",
                font=("Times New Roman", 11, "italic"),
                fill=self.text_color,
            )
            self.questline_canvas.config(scrollregion=self.questline_canvas.bbox("all"))
            # Sidebar hint
            if self.questline_sidebar_frame is not None:
                for child in self.questline_sidebar_frame.winfo_children():
                    child.destroy()
                tk.Label(
                    self.questline_sidebar_frame,
                    text="No quest selected.\nUse the Calendar tab to create a questline.",
                    font=("Times New Roman", 10, "italic"),
                    bg=self.paper_color,
                    fg=self.text_color,
                    justify=tk.LEFT,
                ).pack(anchor="nw", padx=5, pady=5)
            return

        # Sort by importance (desc) then hours (desc) to determine path order
        entries.sort(
            key=lambda e: (
                -getattr(e.get("task"), "importance", 5),
                -(e.get("hours", 0.0) or 0.0),
            )
        )

        # Determine the "current" quest: first not completed
        current_index = None
        for i, entry in enumerate(entries):
            task = entry.get("task")
            if task and not task.completed:
                current_index = i
                break

        # Default selected quest for sidebar
        self.questline_selected_task = None
        if current_index is not None:
            self.questline_selected_task = entries[current_index].get("task")
        elif entries:
            self.questline_selected_task = entries[0].get("task")

        # Draw treasure map style path
        margin_x = 60
        margin_y = 60
        spacing_x = 200
        spacing_y = 160
        max_per_row = 3

        # Start marker
        start_x = margin_x
        start_y = margin_y
        self.questline_canvas.create_oval(
            start_x - 25,
            start_y - 25,
            start_x + 25,
            start_y + 25,
            fill=self.bg_color,
            outline=self.text_color,
            width=2,
        )
        self.questline_canvas.create_text(
            start_x,
            start_y,
            text="START",
            font=("Times New Roman", 11, "bold"),
            fill=self.paper_color,
        )

        prev_x, prev_y = start_x, start_y
        canvas_height = start_y

        for idx, entry in enumerate(entries):
            task = entry.get("task")
            hours = entry.get("hours", 0.0) or 0.0
            if not task:
                continue

            row = idx // max_per_row
            col = idx % max_per_row
            x = margin_x + (col + 1) * spacing_x
            y = margin_y + row * spacing_y

            # Draw path line with little kinks to feel like a map
            mid_x = (prev_x + x) / 2
            self.questline_canvas.create_line(
                prev_x,
                prev_y,
                mid_x,
                prev_y + 15,
                x,
                y,
                fill=self.text_color,
                width=2,
                smooth=True,
            )

            # Determine styling based on completion / current
            is_completed = task.completed
            is_current = current_index is not None and idx == current_index

            if is_completed:
                fill = "#d0c7a1"
                outline = "#888888"
                text_color = "#888888"
            elif is_current:
                fill = self.gold_color
                outline = self.bg_color
                text_color = self.bg_color
            else:
                fill = self.paper_color
                outline = self.text_color
                text_color = self.text_color

            # Draw node as a treasure marker
            box_width = 150
            box_height = 70
            left = x - box_width / 2
            top = y - box_height / 2
            right = x + box_width / 2
            bottom = y + box_height / 2

            rect_id = self.questline_canvas.create_rectangle(
                left,
                top,
                right,
                bottom,
                fill=fill,
                outline=outline,
                width=2,
            )

            title_text = task.title[:22] + ("..." if len(task.title) > 22 else "")
            imp = getattr(task, "importance", 5)
            line1 = f"{title_text}"
            if hours > 0:
                line2 = f"~{hours:g}h  •  {imp}/10"
            else:
                line2 = f"{imp}/10 importance"

            self.questline_canvas.create_text(
                x,
                y - 10,
                text=line1,
                font=("Times New Roman", 11, "bold"),
                fill=text_color,
            )
            self.questline_canvas.create_text(
                x,
                y + 10,
                text=line2,
                font=("Times New Roman", 9),
                fill=text_color,
            )

            # Click to select quest and show in sidebar
            self.questline_canvas.tag_bind(
                rect_id,
                "<Button-1>",
                lambda event, t=task: self.questline_select_from_map(t),
            )

            node_index = len(self.questline_task_map)
            self.questline_task_map[node_index] = task

            prev_x, prev_y = x, y
            canvas_height = max(canvas_height, bottom + margin_y)

        self.questline_canvas.config(scrollregion=(0, 0, margin_x + spacing_x * max_per_row, canvas_height))

        hint = tk.Label(
            inner,
            text="Tip: Click a quest node on the map to view details and submit proof. Only approved proof can complete a quest.",
            font=("Times New Roman", 9, "italic"),
            bg=self.paper_color,
            fg=self.text_color,
        )
        hint.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Build sidebar for selected quest
        self.build_questline_sidebar(self.questline_selected_task)

    def questline_select_from_map(self, task: Task):
        """Handle selecting a quest from the map."""
        self.questline_selected_task = task
        self.build_questline_sidebar(task)

    def build_questline_sidebar(self, task: Optional[Task]):
        """Build or refresh the sidebar with quest details and proof of completion."""
        if self.questline_sidebar_frame is None:
            return

        for child in self.questline_sidebar_frame.winfo_children():
            child.destroy()

        if task is None:
            tk.Label(
                self.questline_sidebar_frame,
                text="Select a quest on the map to view details.",
                font=("Times New Roman", 10, "italic"),
                bg=self.paper_color,
                fg=self.text_color,
                justify=tk.LEFT,
            ).pack(anchor="nw", padx=5, pady=5)
            return

        title = tk.Label(
            self.questline_sidebar_frame,
            text=task.title,
            font=("Times New Roman", 12, "bold"),
            bg=self.paper_color,
            fg=self.text_color,
            wraplength=220,
            justify=tk.LEFT,
        )
        title.pack(anchor="nw", padx=5, pady=(0, 5))

        if task.description:
            desc = tk.Label(
                self.questline_sidebar_frame,
                text=task.description,
                font=("Times New Roman", 9),
                bg=self.paper_color,
                fg=self.text_color,
                wraplength=220,
                justify=tk.LEFT,
            )
            desc.pack(anchor="nw", padx=5, pady=(0, 8))

        # Review status
        status = getattr(task, "proof_status", "unreviewed")
        status_map = {
            "approved": "Approved",
            "rejected": "Rejected",
            "unreviewed": "Not reviewed",
        }
        status_text = status_map.get(status, "Not reviewed")
        status_label = tk.Label(
            self.questline_sidebar_frame,
            text=f"Review status: {status_text}",
            font=("Times New Roman", 9, "bold"),
            bg=self.paper_color,
            fg=self.text_color,
        )
        status_label.pack(anchor="nw", padx=5, pady=(0, 3))

        feedback = getattr(task, "proof_feedback", "")
        if feedback:
            feedback_label = tk.Label(
                self.questline_sidebar_frame,
                text=feedback,
                font=("Times New Roman", 8, "italic"),
                bg=self.paper_color,
                fg=self.text_color,
                wraplength=220,
                justify=tk.LEFT,
            )
            feedback_label.pack(anchor="nw", padx=5, pady=(0, 5))

        proof_label = tk.Label(
            self.questline_sidebar_frame,
            text="Proof type:",
            font=("Times New Roman", 10, "bold"),
            bg=self.paper_color,
            fg=self.text_color,
        )
        proof_label.pack(anchor="nw", padx=5, pady=(0, 3))

        mode = getattr(task, "proof_mode", "text")
        mode_var = tk.StringVar(value=mode if mode in ("text", "image") else "text")

        mode_frame = tk.Frame(self.questline_sidebar_frame, bg=self.paper_color)
        mode_frame.pack(anchor="nw", padx=5, pady=(0, 5))

        def set_mode(new_mode: str):
            task.proof_mode = new_mode
            self.save_data()
            self.build_questline_sidebar(task)

        tk.Radiobutton(
            mode_frame,
            text="Text",
            variable=mode_var,
            value="text",
            command=lambda: set_mode("text"),
            font=("Times New Roman", 9),
            bg=self.paper_color,
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            mode_frame,
            text="Image",
            variable=mode_var,
            value="image",
            command=lambda: set_mode("image"),
            font=("Times New Roman", 9),
            bg=self.paper_color,
        ).pack(side=tk.LEFT, padx=(10, 0))

        # Text proof
        proof_text_frame = tk.Frame(self.questline_sidebar_frame, bg=self.paper_color)
        proof_text = tk.Text(
            proof_text_frame,
            height=6,
            width=30,
            font=("Times New Roman", 9),
            bg=self.paper_color,
            fg=self.text_color,
            wrap=tk.WORD,
        )
        proof_text.pack(anchor="nw")
        existing_text = getattr(task, "proof_text", "")
        if existing_text:
            proof_text.insert("1.0", existing_text)

        # Image path (stored as text)
        image_frame = tk.Frame(self.questline_sidebar_frame, bg=self.paper_color)
        tk.Label(
            image_frame,
            text="Image proof (path):",
            font=("Times New Roman", 9, "bold"),
            bg=self.paper_color,
            fg=self.text_color,
        ).pack(anchor="nw")

        image_var = tk.StringVar(value=getattr(task, "proof_image", ""))
        image_entry = tk.Entry(
            image_frame,
            textvariable=image_var,
            font=("Times New Roman", 9),
            width=28,
            bg=self.paper_color,
            fg=self.text_color,
            relief=tk.SUNKEN,
        )
        image_entry.pack(side=tk.LEFT, pady=(0, 5))

        # Show only the selected proof input
        if mode_var.get() == "text":
            proof_text_frame.pack(anchor="nw", padx=5, pady=(0, 5))
        else:
            image_frame.pack(anchor="nw", padx=5, pady=(0, 5), fill=tk.X)

        btn_frame = tk.Frame(self.questline_sidebar_frame, bg=self.paper_color)
        btn_frame.pack(anchor="se", fill=tk.X, padx=5, pady=(5, 0))

        verify_btn = tk.Button(
            btn_frame,
            text="Verify Proof",
            command=lambda t=task: self.verify_proof_with_ai(
                t,
                mode_var.get(),
                proof_text.get("1.0", tk.END).strip(),
                image_var.get().strip(),
            ),
            font=("Times New Roman", 9),
            bg=self.accent_color,
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2",
        )
        verify_btn.pack(side=tk.RIGHT, padx=(5, 0))

    def verify_proof_with_ai(self, task: Task, mode: Optional[str] = None, text_value: Optional[str] = None, image_value: Optional[str] = None):
        """Simulate an AI agent verifying the provided proof against the quest and mark completion on approval."""
        if mode is None:
            mode = getattr(task, "proof_mode", "text")
        if mode not in ("text", "image"):
            mode = "text"

        # Persist latest proof values
        if text_value is not None:
            task.proof_text = text_value
        if image_value is not None:
            task.proof_image = image_value
        task.proof_mode = mode

        # Default state
        status = "rejected"
        feedback = "Proof could not be verified. Please provide more detailed evidence."

        title = (task.title or "").lower()
        description = (task.description or "").lower()

        if mode == "text":
            text = (text_value if text_value is not None else getattr(task, "proof_text", "")).strip()
            if not text:
                feedback = "No text proof provided. Please describe what you completed."
            elif len(text) < 20:
                feedback = "Your explanation is very short. Please add more detail about what you did."
            else:
                # Simple semantic check: look for title/description keywords in the explanation
                import re

                def keywords(s: str):
                    return [w for w in re.findall(r"[A-Za-z]{4,}", s.lower())]

                quest_keywords = set(keywords(title) + keywords(description))
                proof_keywords = set(keywords(text))

                overlap = quest_keywords.intersection(proof_keywords)

                if quest_keywords and not overlap:
                    feedback = (
                        "Your explanation does not mention anything clearly related to this quest. "
                        "Please reference what the quest asked you to do."
                    )
                else:
                    status = "approved"
                    feedback = (
                        "Your explanation appears consistent with this quest. "
                        "Chronos accepts this as proof of completion."
                    )

        else:  # image mode
            path = (image_value if image_value is not None else getattr(task, "proof_image", "")).strip()
            if not path:
                feedback = "No image path provided. Please add a path to an image showing your progress."
            elif not os.path.exists(path):
                feedback = "The image file could not be found. Please check the path and try again."
            else:
                status = "approved"
                feedback = (
                    "An image was provided and appears to be present on disk. "
                    "Chronos tentatively accepts this as proof (no deep image analysis is performed)."
                )

        task.proof_status = status
        task.proof_feedback = feedback
        if status == "approved":
            task.completed = True
        self.save_data()
        if self.questline_parent is not None:
            self.build_questline_tab(self.questline_parent)

    def build_calendar_tab(self, parent: tk.Frame):
        # Remember parent so we can redraw when navigating
        self.calendar_parent = parent

        # Clear any existing calendar content
        for widget in parent.winfo_children():
            widget.destroy()

        calendar_frame = tk.Frame(parent, bg=self.paper_color, relief=tk.RAISED, bd=3)
        calendar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Navigation row with previous/next month
        nav_frame = tk.Frame(calendar_frame, bg=self.paper_color)
        nav_frame.grid(row=0, column=0, columnspan=7, pady=(5, 10))

        prev_btn = tk.Button(
            nav_frame,
            text="◀",
            font=("Times New Roman", 12, "bold"),
            bg=self.paper_color,
            fg=self.text_color,
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.change_month(-1),
        )
        prev_btn.pack(side=tk.LEFT, padx=10)

        month_name = calendar.month_name[self.calendar_month]
        year = self.calendar_year

        header_label = tk.Label(
            nav_frame,
            text=f"{month_name} {year}",
            font=("Times New Roman", 18, "bold"),
            bg=self.paper_color,
            fg=self.text_color,
        )
        header_label.pack(side=tk.LEFT, padx=10)

        next_btn = tk.Button(
            nav_frame,
            text="▶",
            font=("Times New Roman", 12, "bold"),
            bg=self.paper_color,
            fg=self.text_color,
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.change_month(1),
        )
        next_btn.pack(side=tk.LEFT, padx=10)

        # Today indicator
        today_label = tk.Label(
            calendar_frame,
            text=f"Today: {self.today.strftime('%A, %B %d, %Y')}",
            font=("Times New Roman", 11, "italic"),
            bg=self.paper_color,
            fg=self.green_color,
        )
        today_label.grid(row=1, column=0, columnspan=7, pady=(0, 10))

        # Weekday headers
        for idx, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            lbl = tk.Label(
                calendar_frame,
                text=day_name,
                font=("Times New Roman", 12, "bold"),
                bg=self.paper_color,
                fg=self.text_color,
            )
            lbl.grid(row=2, column=idx, padx=8, pady=4)

        # Days of current calendar month (boxed, selectable)
        cal = calendar.Calendar(firstweekday=0)  # Monday
        month_days = cal.monthdayscalendar(year, self.calendar_month)

        for week_idx, week in enumerate(month_days):
            for day_idx, day in enumerate(week):
                if day == 0:
                    text = ""
                else:
                    text = str(day)

                is_today = (
                    day
                    and self.today.day == day
                    and self.today.month == self.calendar_month
                    and self.today.year == year
                )

                is_selected = (
                    day
                    and self.selected_date.year == year
                    and self.selected_date.month == self.calendar_month
                    and self.selected_date.day == day
                )

                # Mark days that have a scheduled plan
                has_plan = False
                if day:
                    try:
                        date_for_day = datetime(year, self.calendar_month, day).date()
                        has_plan = date_for_day.isoformat() in self.scheduled_plan
                    except ValueError:
                        has_plan = False

                if is_today:
                    bg = self.gold_color
                    fg = self.bg_color
                elif is_selected:
                    bg = self.green_color
                    fg = "white"
                else:
                    bg = self.paper_color
                    fg = self.text_color

                display_text = text
                if has_plan and text:
                    display_text = f"{text}★"

                lbl = tk.Label(
                    calendar_frame,
                    text=display_text,
                    width=5,
                    height=3,
                    font=("Times New Roman", 12),
                    bg=bg,
                    fg=fg,
                    relief=tk.RIDGE if text else tk.FLAT,
                    bd=2 if text else 0,
                )
                lbl.grid(row=3 + week_idx, column=day_idx, padx=6, pady=6, sticky="nsew")

                # Make date boxes clickable/selectable
                if day != 0:
                    lbl.bind(
                        "<Button-1>",
                        lambda event, d=day: self.on_calendar_day_click(d),
                    )

        # Daily schedule details panel for selected date
        details_row = 3 + len(month_days)
        details_frame = tk.Frame(calendar_frame, bg=self.paper_color)
        details_frame.grid(row=details_row, column=0, columnspan=7, sticky="nsew", pady=(10, 0))

        date_for_details = self.selected_date or self.today
        date_key = date_for_details.isoformat()
        header = tk.Label(
            details_frame,
            text=f"Schedule for {date_for_details.strftime('%A, %B %d, %Y')}:",
            font=("Times New Roman", 11, "bold"),
            bg=self.paper_color,
            fg=self.text_color,
        )
        header.pack(anchor=tk.W)

        entries = self.scheduled_plan.get(date_key, [])
        if not entries:
            no_label = tk.Label(
                details_frame,
                text="No quests scheduled for this day.",
                font=("Times New Roman", 10, "italic"),
                bg=self.paper_color,
                fg=self.green_color,
            )
            no_label.pack(anchor=tk.W, pady=(2, 0))
        else:
            for entry in entries:
                task = entry.get("task")
                hours = entry.get("hours", 0.0) or 0.0
                if not task:
                    continue
                imp = getattr(task, "importance", 5)
                label = tk.Label(
                    details_frame,
                    text=f"- {task.title} (~{hours:g}h, importance {imp}/10)",
                    font=("Times New Roman", 10),
                    bg=self.paper_color,
                    fg=self.text_color,
                )
                label.pack(anchor=tk.W)

        # Create Questline button at the bottom of the calendar
        last_row = details_row + 1
        questline_btn = tk.Button(
            calendar_frame,
            text="Create Questline",
            font=("Times New Roman", 11, "bold"),
            bg=self.green_color,
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2",
            command=self.open_questline_wizard,
        )
        questline_btn.grid(row=last_row, column=0, columnspan=7, pady=(10, 0))

    def change_month(self, delta: int):
        """Move calendar forward/backward by given number of months."""
        month = self.calendar_month + delta
        year = self.calendar_year

        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1

        self.calendar_month = month
        self.calendar_year = year
        if self.calendar_parent is not None:
            self.build_calendar_tab(self.calendar_parent)

    def on_calendar_day_click(self, day: int):
        """Handle selecting a day in the calendar."""
        try:
            self.selected_date = datetime(self.calendar_year, self.calendar_month, day).date()
        except ValueError:
            return
        if self.calendar_parent is not None:
            self.build_calendar_tab(self.calendar_parent)

    def open_questline_wizard(self):
        """Open a new window that narrates an AI-style optimized questline and builds a schedule."""
        # Build an optimized schedule first
        self.scheduled_plan = {}

        start_date = self.selected_date or self.today
        active_tasks = [t for t in self.tasks if not t.completed]

        def add_to_plan(d: datetime.date, task: Task, hours: float):
            key = d.isoformat()
            if hours <= 0:
                return
            self.scheduled_plan.setdefault(key, []).append({"task": task, "hours": round(hours, 2)})

        for task in active_tasks:
            hours = getattr(task, "approximate_hours", 0.0) or 0.0
            if hours <= 0:
                hours = 1.0  # default if no estimate provided

            section = getattr(task, "section", "Daily") or "Daily"

            if section == "Weekly":
                # Spread work over 7 days starting from the selected date
                total = float(hours)
                per_day = total / 7.0
                remaining = total
                for i in range(7):
                    day_hours = round(per_day, 2)
                    if i == 6:
                        day_hours = round(remaining, 2)
                    remaining -= day_hours
                    day_date = start_date + timedelta(days=i)
                    add_to_plan(day_date, task, day_hours)
            elif section == "Daily":
                # Focus this quest on the selected day
                add_to_plan(start_date, task, hours)
            elif section == "Monthly":
                # Simple approach: schedule on the selected day for now
                add_to_plan(start_date, task, hours)
            else:
                add_to_plan(start_date, task, hours)

        # Refresh calendar so stars and daily schedule reflect the plan
        if self.calendar_parent is not None:
            self.build_calendar_tab(self.calendar_parent)
        if self.questline_parent is not None:
            self.build_questline_tab(self.questline_parent)

        # Now present the AI "wizard" narrative
        wizard = tk.Toplevel(self.root)
        wizard.title("Questline Wizard")
        wizard.geometry("700x500")
        wizard.configure(bg=self.bg_color)
        wizard.transient(self.root)
        wizard.grab_set()

        # Center the wizard window
        wizard.update_idletasks()
        w = 700
        h = 500
        x = (wizard.winfo_screenwidth() // 2) - (w // 2)
        y = (wizard.winfo_screenheight() // 2) - (h // 2)
        wizard.geometry(f"{w}x{h}+{x}+{y}")

        main_frame = tk.Frame(wizard, bg=self.paper_color, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = tk.Label(
            main_frame,
            text="Chronos, the Time Sage",
            font=("Times New Roman", 18, "bold"),
            bg=self.paper_color,
            fg=self.text_color,
        )
        title_label.pack(pady=(0, 10))

        subtitle_label = tk.Label(
            main_frame,
            text="\"I am an ancient planner spirit. Let me weave your quests into time.\"",
            font=("Times New Roman", 11, "italic"),
            bg=self.paper_color,
            fg=self.green_color,
        )
        subtitle_label.pack(pady=(0, 10))

        # Build a narrative based on the computed schedule
        if self.selected_date:
            anchor_day = self.selected_date
        else:
            anchor_day = self.today
        day_str = anchor_day.strftime("%A, %B %d, %Y")

        lines = []
        if not self.scheduled_plan:
            lines.append(
                f"Greetings, adventurer. On {day_str}, your ledger of quests is empty.\n"
                "The winds are calm, and no tasks call for your attention just yet."
            )
        else:
            lines.append(
                f"Greetings, adventurer. I, Chronos the Time Sage, have walked the river of hours from {day_str} onward.\n"
                "I have divided your quests by importance and the time they demand, and placed them upon the days ahead."
            )

            total_hours = 0.0
            for date_key in sorted(self.scheduled_plan.keys()):
                try:
                    d = datetime.fromisoformat(date_key).date()
                except ValueError:
                    continue
                entries = self.scheduled_plan[date_key]
                day_total = sum(e.get("hours", 0.0) or 0.0 for e in entries)
                total_hours += day_total
                lines.append(f"\nOn {d.strftime('%A, %B %d, %Y')}, focus on:")
                for entry in entries:
                    task = entry.get("task")
                    hours = entry.get("hours", 0.0) or 0.0
                    if not task:
                        continue
                    imp = getattr(task, "importance", 5)
                    section = getattr(task, "section", 'Daily')
                    lines.append(
                        f"  • {task.title} (~{hours:g}h, importance {imp}/10, rhythm: {section})"
                    )
                    if task.description:
                        lines.append(f"    \"{task.description}\"")

            lines.append(
                "\nWalk this path, and you will honor both urgency and your finite strength."
            )
            if total_hours > 0:
                lines.append(
                    f"In all, this questline spans roughly {total_hours:g} hours of focused effort."
                )

        narrative = "\n".join(lines)

        text_frame = tk.Frame(main_frame, bg=self.paper_color)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 10))

        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Times New Roman", 11),
            bg=self.paper_color,
            fg=self.text_color,
        )
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scroll.set)

        text_widget.insert("1.0", narrative)
        text_widget.config(state=tk.DISABLED)

        btn_frame = tk.Frame(main_frame, bg=self.paper_color)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        close_btn = tk.Button(
            btn_frame,
            text="Close",
            command=wizard.destroy,
            font=("Times New Roman", 10),
            bg="#8B0000",
            fg="white",
            relief=tk.RAISED,
            bd=2,
            cursor="hand2",
        )
        close_btn.pack(side=tk.RIGHT)
    
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
        
        # Tabs for Quests, Calendar, and Questline
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        quests_tab = tk.Frame(notebook, bg=self.bg_color)
        calendar_tab = tk.Frame(notebook, bg=self.bg_color)
        questline_tab = tk.Frame(notebook, bg=self.bg_color)

        notebook.add(quests_tab, text="Quests")
        notebook.add(calendar_tab, text="Calendar")
        notebook.add(questline_tab, text="Questline")
        
        # Quests content area with two columns
        content_frame = tk.Frame(quests_tab, bg=self.bg_color)
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

        # Calendar tab content (navigable, selectable calendar)
        self.build_calendar_tab(calendar_tab)

        # Questline tab content (today's scheduled quests, completion control)
        self.build_questline_tab(questline_tab)
    
    def add_task(self):
        dialog = TaskDialog(
            self.root,
            "Add New Quest",
            labels=list(self.labels.keys()),
            sections=self.sections,
        )
        self.root.wait_window(dialog.dialog)
        if dialog.result:
            title, description, selected_labels, section, importance, approx_hours = dialog.result
            task = Task(
                title,
                description,
                selected_labels,
                section=section,
                importance=importance,
                approximate_hours=approx_hours,
            )
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
            sections=self.sections,
            initial_title=task.title,
            initial_description=task.description,
            initial_labels=task.labels,
            initial_section=getattr(task, "section", "Daily"),
            initial_importance=getattr(task, "importance", 5),
            initial_approx_hours=getattr(task, "approximate_hours", 0.0),
        )
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            title, description, selected_labels, section, importance, approx_hours = dialog.result
            task.title = title
            task.description = description
            task.labels = selected_labels
            task.section = section or "Daily"
            task.importance = max(1, min(int(importance), 10))
            try:
                task.approximate_hours = max(0.0, float(approx_hours))
            except (TypeError, ValueError):
                task.approximate_hours = 0.0
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
        messagebox.showinfo(
            "Completion Locked",
            "Quests can only be completed by submitting proof on the Questline tab and having it approved by Chronos.",
        )
    
    def get_selected_task(self) -> Optional[Task]:
        selection = self.task_listbox.curselection()
        if not selection:
            return None
        
        index = selection[0]
        if not hasattr(self, 'display_task_map'):
            return None
        return self.display_task_map.get(index)
    
    def get_filtered_tasks(self) -> List[Task]:
        if self.filter_label:
            return [t for t in self.tasks if self.filter_label in t.labels]
        return self.tasks
    
    def update_task_list(self):
        if not hasattr(self, 'task_listbox'):
            return
        self.task_listbox.delete(0, tk.END)
        self.display_task_map = {}
        filtered_tasks = self.get_filtered_tasks()
        
        # Group tasks by section (Daily / Weekly / Monthly)
        section_to_tasks: Dict[str, List[Task]] = {}
        for task in filtered_tasks:
            section = getattr(task, "section", "Daily") or "Daily"
            section_to_tasks.setdefault(section, []).append(task)

        idx = 0
        sections_order = self.sections or ["Daily", "Weekly", "Monthly"]
        for section in sections_order:
            tasks_in_section = section_to_tasks.get(section, [])
            if not tasks_in_section:
                continue

            header_text = f"--- {section} Quests ---"
            self.task_listbox.insert(tk.END, header_text)
            self.task_listbox.itemconfig(
                idx,
                {'fg': self.green_color}
            )
            self.display_task_map[idx] = None
            idx += 1

            for task in tasks_in_section:
                # Build display string with labels
                label_str = " ".join(
                    [self.labels[label].symbol for label in task.labels if label in self.labels]
                )
                if label_str:
                    label_str = label_str + " "
                status = "✅" if task.completed else "⭕"
                importance = getattr(task, "importance", 5)
                approx_hours = getattr(task, "approximate_hours", 0.0)
                display = f"{status} [{importance}/10] {label_str}{task.title}"
                if task.description:
                    display += f" - {task.description[:30]}..."
                if approx_hours and approx_hours > 0:
                    display += f" (~{approx_hours:g}h)"
                
                self.task_listbox.insert(tk.END, display)
                self.display_task_map[idx] = task
                
                # Style completed tasks differently
                if task.completed:
                    self.task_listbox.itemconfig(idx, {'fg': '#888888'})

                idx += 1
    
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
    def __init__(
        self,
        parent,
        title,
        labels=None,
        sections=None,
            initial_title="",
            initial_description="",
            initial_labels=None,
            initial_section="Daily",
            initial_importance: int = 5,
            initial_approx_hours: float = 0.0,
    ):
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
        
        # Section
        tk.Label(
            main_frame,
            text="Quest Rhythm:",
            font=("Times New Roman", 11, "bold"),
            bg="#F4E4BC",
            fg="#3D2817"
        ).pack(anchor=tk.W, pady=(0, 5))

        section_frame = tk.Frame(main_frame, bg="#F4E4BC")
        section_frame.pack(fill=tk.X, pady=(0, 15))

        available_sections = sections or ["Daily", "Weekly", "Monthly"]
        default_section = initial_section if initial_section in available_sections else available_sections[0]
        self.section_var = tk.StringVar(value=default_section)

        section_menu = tk.OptionMenu(section_frame, self.section_var, *available_sections)
        section_menu.config(font=("Times New Roman", 10), bg="#F4E4BC")
        section_menu["menu"].config(font=("Times New Roman", 10))
        section_menu.pack(side=tk.LEFT, anchor=tk.W)

        # Importance slider
        tk.Label(
            main_frame,
            text="Importance (1-10):",
            font=("Times New Roman", 11, "bold"),
            bg="#F4E4BC",
            fg="#3D2817"
        ).pack(anchor=tk.W, pady=(0, 5))

        importance_frame = tk.Frame(main_frame, bg="#F4E4BC")
        importance_frame.pack(fill=tk.X, pady=(0, 15))

        self.importance_var = tk.IntVar(value=max(1, min(int(initial_importance), 10)))

        importance_scale = tk.Scale(
            importance_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.importance_var,
            bg="#F4E4BC",
            fg="#3D2817",
            troughcolor="#D4AF37",
            highlightthickness=0,
            length=250,
        )
        importance_scale.pack(side=tk.LEFT, padx=(0, 10))

        importance_hint = tk.Label(
            importance_frame,
            text="1 = low, 10 = super important",
            font=("Times New Roman", 9, "italic"),
            bg="#F4E4BC",
            fg="#3D2817",
        )
        importance_hint.pack(side=tk.LEFT)

        # Approximate hours
        tk.Label(
            main_frame,
            text="Approximate Hours:",
            font=("Times New Roman", 11, "bold"),
            bg="#F4E4BC",
            fg="#3D2817"
        ).pack(anchor=tk.W, pady=(0, 5))

        hours_frame = tk.Frame(main_frame, bg="#F4E4BC")
        hours_frame.pack(fill=tk.X, pady=(0, 15))

        self.approx_hours_var = tk.DoubleVar()
        try:
            self.approx_hours_var.set(max(0.0, float(initial_approx_hours)))
        except (TypeError, ValueError):
            self.approx_hours_var.set(0.0)

        hours_spin = tk.Spinbox(
            hours_frame,
            from_=0.0,
            to=1000.0,
            increment=0.5,
            textvariable=self.approx_hours_var,
            width=8,
            font=("Times New Roman", 11),
        )
        hours_spin.pack(side=tk.LEFT, padx=(0, 10))

        hours_hint = tk.Label(
            hours_frame,
            text="Estimate how many hours this quest will take.",
            font=("Times New Roman", 9, "italic"),
            bg="#F4E4BC",
            fg="#3D2817",
        )
        hours_hint.pack(side=tk.LEFT)

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
            text="Add to Schedule",
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

        # Keyboard shortcuts for saving while editing
        self.title_entry.bind("<Return>", lambda event: self.save())
        self.dialog.bind("<Control-s>", lambda event: self.save())
    
    def save(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Invalid", "Quest title cannot be empty.")
            return
        
        description = self.desc_text.get("1.0", tk.END).strip()
        selected_labels = [name for name, var in self.label_vars.items() if var.get()]
        section = self.section_var.get() if hasattr(self, "section_var") else "Daily"
        importance = self.importance_var.get() if hasattr(self, "importance_var") else 5
        try:
            approx_hours = float(self.approx_hours_var.get()) if hasattr(self, "approx_hours_var") else 0.0
        except (TypeError, ValueError):
            approx_hours = 0.0
        
        self.result = (title, description, selected_labels, section, importance, approx_hours)
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
