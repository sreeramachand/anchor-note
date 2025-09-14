"""
kivy_app.py

Minimal Kivy entrypoint that shows pending tasks count and opens a simple checklist UI.
This is a thin wrapper: the actual business logic lives in core.checklist.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from ..core.checklist import list_pending_tasks, mark_task_done

class MainBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.lbl = Label(text="Sticky Remind (Kivy) — pending: 0")
        self.add_widget(self.lbl)
        Clock.schedule_interval(self.refresh, 5)

    def refresh(self, dt):
        rows = list_pending_tasks()
        self.lbl.text = f"Sticky Remind — pending tasks: {len(rows)}"

class StickyKivyApp(App):
    def build(self):
        return MainBox()

def main():
    StickyKivyApp().run()

if __name__ == "__main__":
    main()
