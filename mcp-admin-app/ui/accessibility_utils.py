"""
Accessibility and Usability Enhancements
========================================

Utilities for improving accessibility and usability of the UI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Any, Callable
import platform


class KeyboardNavigationManager:
    """Manages keyboard navigation for UI components."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.focus_order: List[tk.Widget] = []
        self.current_focus_index = 0
        self.shortcuts: Dict[str, Callable] = {}
        
        # Bind global keyboard events
        self.root.bind_all('<Tab>', self._handle_tab)
        self.root.bind_all('<Shift-Tab>', self._handle_shift_tab)
        self.root.bind_all('<Control-Key>', self._handle_control_key)
        self.root.bind_all('<Alt-Key>', self._handle_alt_key)
        
        # Platform-specific bindings
        if platform.system() == "Darwin":  # macOS
            self.root.bind_all('<Command-Key>', self._handle_command_key)
    
    def register_widget(self, widget: tk.Widget, tab_order: int = None):
        """Register widget for keyboard navigation."""
        if tab_order is not None:
            # Insert at specific position
            self.focus_order.insert(tab_order, widget)
        else:
            # Append to end
            self.focus_order.append(widget)
        
        # Enable keyboard focus
        if hasattr(widget, 'configure'):
            try:
                widget.configure(takefocus=True)
            except tk.TclError:
                pass  # Some widgets don't support takefocus
    
    def register_shortcut(self, key_combination: str, callback: Callable):
        """Register keyboard shortcut."""
        self.shortcuts[key_combination.lower()] = callback
    
    def _handle_tab(self, event):
        """Handle Tab key for forward navigation."""
        if self.focus_order:
            self.current_focus_index = (self.current_focus_index + 1) % len(self.focus_order)
            next_widget = self.focus_order[self.current_focus_index]
            
            if next_widget.winfo_exists() and str(next_widget['state']) != 'disabled':
                next_widget.focus_set()
                return "break"
    
    def _handle_shift_tab(self, event):
        """Handle Shift+Tab for backward navigation."""
        if self.focus_order:
            self.current_focus_index = (self.current_focus_index - 1) % len(self.focus_order)
            prev_widget = self.focus_order[self.current_focus_index]
            
            if prev_widget.winfo_exists() and str(prev_widget['state']) != 'disabled':
                prev_widget.focus_set()
                return "break"
    
    def _handle_control_key(self, event):
        """Handle Ctrl+Key combinations."""
        key_combo = f"ctrl+{event.keysym.lower()}"
        if key_combo in self.shortcuts:
            self.shortcuts[key_combo]()
            return "break"
    
    def _handle_alt_key(self, event):
        """Handle Alt+Key combinations."""
        key_combo = f"alt+{event.keysym.lower()}"
        if key_combo in self.shortcuts:
            self.shortcuts[key_combo]()
            return "break"
    
    def _handle_command_key(self, event):
        """Handle Cmd+Key combinations (macOS)."""
        key_combo = f"cmd+{event.keysym.lower()}"
        if key_combo in self.shortcuts:
            self.shortcuts[key_combo]()
            return "break"


class TooltipManager:
    """Manages tooltips for UI components."""
    
    def __init__(self):
        self.tooltips: Dict[tk.Widget, 'Tooltip'] = {}
    
    def add_tooltip(self, widget: tk.Widget, text: str, delay: int = 500):
        """Add tooltip to widget."""
        tooltip = Tooltip(widget, text, delay)
        self.tooltips[widget] = tooltip
        return tooltip
    
    def remove_tooltip(self, widget: tk.Widget):
        """Remove tooltip from widget."""
        if widget in self.tooltips:
            self.tooltips[widget].destroy()
            del self.tooltips[widget]
    
    def update_tooltip(self, widget: tk.Widget, text: str):
        """Update tooltip text."""
        if widget in self.tooltips:
            self.tooltips[widget].update_text(text)


class Tooltip:
    """Individual tooltip implementation."""
    
    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.show_job = None
        
        # Bind events
        self.widget.bind('<Enter>', self._on_enter)
        self.widget.bind('<Leave>', self._on_leave)
        self.widget.bind('<Motion>', self._on_motion)
    
    def _on_enter(self, event):
        """Handle mouse enter."""
        self._schedule_show()
    
    def _on_leave(self, event):
        """Handle mouse leave."""
        self._cancel_show()
        self._hide()
    
    def _on_motion(self, event):
        """Handle mouse motion."""
        self._cancel_show()
        self._schedule_show()
    
    def _schedule_show(self):
        """Schedule tooltip to show after delay."""
        self._cancel_show()
        self.show_job = self.widget.after(self.delay, self._show)
    
    def _cancel_show(self):
        """Cancel scheduled tooltip show."""
        if self.show_job:
            self.widget.after_cancel(self.show_job)
            self.show_job = None
    
    def _show(self):
        """Show tooltip."""
        if self.tooltip_window:
            return
        
        # Get widget position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip content
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9),
            wraplength=300
        )
        label.pack()
    
    def _hide(self):
        """Hide tooltip."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def update_text(self, text: str):
        """Update tooltip text."""
        self.text = text
        if self.tooltip_window:
            self._hide()
    
    def destroy(self):
        """Destroy tooltip."""
        self._cancel_show()
        self._hide()
        
        # Unbind events
        try:
            self.widget.unbind('<Enter>')
            self.widget.unbind('<Leave>')
            self.widget.unbind('<Motion>')
        except tk.TclError:
            pass


class ResponsiveLayout:
    """Manages responsive layouts for different screen sizes."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.layouts: Dict[str, Dict[str, Any]] = {}
        self.current_layout = "default"
        self.min_width = 800
        self.min_height = 600
        
        # Bind resize events
        self.root.bind('<Configure>', self._on_window_resize)
        
        # Set minimum size
        self.root.minsize(self.min_width, self.min_height)
    
    def register_layout(self, name: str, min_width: int, min_height: int, 
                       layout_config: Dict[str, Any]):
        """Register a responsive layout configuration."""
        self.layouts[name] = {
            'min_width': min_width,
            'min_height': min_height,
            'config': layout_config
        }
    
    def _on_window_resize(self, event):
        """Handle window resize events."""
        if event.widget != self.root:
            return
        
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # Find best layout
        best_layout = "default"
        for name, layout in self.layouts.items():
            if (width >= layout['min_width'] and 
                height >= layout['min_height']):
                best_layout = name
        
        # Apply layout if changed
        if best_layout != self.current_layout:
            self._apply_layout(best_layout)
            self.current_layout = best_layout
    
    def _apply_layout(self, layout_name: str):
        """Apply responsive layout."""
        if layout_name not in self.layouts:
            return
        
        layout_config = self.layouts[layout_name]['config']
        
        # Apply layout configuration
        for widget_name, config in layout_config.items():
            # This would be implemented based on specific layout needs
            pass


class AccessibilityEnhancer:
    """Enhances accessibility of UI components."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.keyboard_nav = KeyboardNavigationManager(root)
        self.tooltip_manager = TooltipManager()
        self.responsive_layout = ResponsiveLayout(root)
        
        # High contrast mode
        self.high_contrast_mode = False
        self.original_colors = {}
        
        # Font scaling
        self.font_scale = 1.0
        self.original_fonts = {}
        
        self._setup_accessibility_shortcuts()
    
    def _setup_accessibility_shortcuts(self):
        """Set up accessibility keyboard shortcuts."""
        # Toggle high contrast
        self.keyboard_nav.register_shortcut('ctrl+shift+h', self.toggle_high_contrast)
        
        # Font scaling
        self.keyboard_nav.register_shortcut('ctrl+plus', self.increase_font_size)
        self.keyboard_nav.register_shortcut('ctrl+minus', self.decrease_font_size)
        self.keyboard_nav.register_shortcut('ctrl+0', self.reset_font_size)
    
    def enhance_widget(self, widget: tk.Widget, 
                      tooltip_text: str = None,
                      keyboard_shortcut: str = None,
                      shortcut_callback: Callable = None,
                      tab_order: int = None):
        """Enhance widget with accessibility features."""
        
        # Add to keyboard navigation
        if tab_order is not None or widget.winfo_class() in ['Entry', 'Text', 'Button', 'Checkbutton', 'Radiobutton']:
            self.keyboard_nav.register_widget(widget, tab_order)
        
        # Add tooltip
        if tooltip_text:
            self.tooltip_manager.add_tooltip(widget, tooltip_text)
        
        # Add keyboard shortcut
        if keyboard_shortcut and shortcut_callback:
            self.keyboard_nav.register_shortcut(keyboard_shortcut, shortcut_callback)
        
        # Store original styling for high contrast mode
        self._store_original_styling(widget)
    
    def _store_original_styling(self, widget: tk.Widget):
        """Store original widget styling."""
        try:
            widget_id = str(widget)
            self.original_colors[widget_id] = {
                'bg': widget.cget('bg') if 'bg' in widget.keys() else None,
                'fg': widget.cget('fg') if 'fg' in widget.keys() else None,
                'selectbackground': widget.cget('selectbackground') if 'selectbackground' in widget.keys() else None,
                'selectforeground': widget.cget('selectforeground') if 'selectforeground' in widget.keys() else None,
            }
            
            if 'font' in widget.keys():
                self.original_fonts[widget_id] = widget.cget('font')
        except tk.TclError:
            pass
    
    def toggle_high_contrast(self):
        """Toggle high contrast mode."""
        self.high_contrast_mode = not self.high_contrast_mode
        
        if self.high_contrast_mode:
            self._apply_high_contrast()
        else:
            self._restore_original_colors()
    
    def _apply_high_contrast(self):
        """Apply high contrast colors."""
        high_contrast_colors = {
            'bg': '#000000',
            'fg': '#ffffff',
            'selectbackground': '#ffffff',
            'selectforeground': '#000000'
        }
        
        self._apply_colors_to_all_widgets(self.root, high_contrast_colors)
    
    def _restore_original_colors(self):
        """Restore original colors."""
        for widget_id, colors in self.original_colors.items():
            try:
                widget = self.root.nametowidget(widget_id)
                for attr, color in colors.items():
                    if color and attr in widget.keys():
                        widget.configure(**{attr: color})
            except (tk.TclError, KeyError):
                pass
    
    def _apply_colors_to_all_widgets(self, parent: tk.Widget, colors: Dict[str, str]):
        """Apply colors to all widgets recursively."""
        try:
            for attr, color in colors.items():
                if attr in parent.keys():
                    parent.configure(**{attr: color})
        except tk.TclError:
            pass
        
        # Apply to children
        for child in parent.winfo_children():
            self._apply_colors_to_all_widgets(child, colors)
    
    def increase_font_size(self):
        """Increase font size."""
        self.font_scale = min(2.0, self.font_scale + 0.1)
        self._apply_font_scaling()
    
    def decrease_font_size(self):
        """Decrease font size."""
        self.font_scale = max(0.5, self.font_scale - 0.1)
        self._apply_font_scaling()
    
    def reset_font_size(self):
        """Reset font size to default."""
        self.font_scale = 1.0
        self._apply_font_scaling()
    
    def _apply_font_scaling(self):
        """Apply font scaling to all widgets."""
        for widget_id, original_font in self.original_fonts.items():
            try:
                widget = self.root.nametowidget(widget_id)
                if original_font:
                    # Parse font and scale size
                    if isinstance(original_font, tuple):
                        family, size = original_font[0], original_font[1]
                        new_size = int(size * self.font_scale)
                        new_font = (family, new_size) + original_font[2:]
                    else:
                        # Handle string font specifications
                        new_font = original_font
                    
                    widget.configure(font=new_font)
            except (tk.TclError, KeyError, IndexError):
                pass


class HelpSystem:
    """Context-sensitive help system."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.help_content: Dict[str, str] = {}
        self.help_window = None
        
        # Bind F1 for help
        self.root.bind_all('<F1>', self._show_context_help)
    
    def register_help(self, widget: tk.Widget, help_text: str):
        """Register help content for a widget."""
        widget_id = str(widget)
        self.help_content[widget_id] = help_text
        
        # Bind right-click for context help
        widget.bind('<Button-3>', lambda e: self._show_help_for_widget(widget))
    
    def _show_context_help(self, event):
        """Show context-sensitive help."""
        focused_widget = self.root.focus_get()
        if focused_widget:
            self._show_help_for_widget(focused_widget)
    
    def _show_help_for_widget(self, widget: tk.Widget):
        """Show help for specific widget."""
        widget_id = str(widget)
        help_text = self.help_content.get(widget_id, "No help available for this component.")
        
        self._show_help_window(help_text)
    
    def _show_help_window(self, help_text: str):
        """Show help window."""
        if self.help_window:
            self.help_window.destroy()
        
        self.help_window = tk.Toplevel(self.root)
        self.help_window.title("Help")
        self.help_window.geometry("500x300")
        self.help_window.transient(self.root)
        
        # Create help content
        text_frame = tk.Frame(self.help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10))
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.insert(1.0, help_text)
        text_widget.configure(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        close_btn = tk.Button(
            self.help_window,
            text="Close",
            command=self.help_window.destroy
        )
        close_btn.pack(pady=10)


# Convenience function to set up accessibility for a window
def setup_accessibility(root: tk.Tk) -> AccessibilityEnhancer:
    """Set up accessibility enhancements for a window."""
    enhancer = AccessibilityEnhancer(root)
    help_system = HelpSystem(root)
    
    # Store references
    root.accessibility_enhancer = enhancer
    root.help_system = help_system
    
    return enhancer