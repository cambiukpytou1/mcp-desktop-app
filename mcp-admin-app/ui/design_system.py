"""
Modern Design System - Substack-Inspired
========================================

A comprehensive design system providing colors, typography, spacing, and components
that create a modern, editorial interface similar to Substack's visual language.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Tuple, Optional, Callable


class DesignSystem:
    """Modern design system with Substack-inspired aesthetics."""
    
    # Color Palette - Dark/neutral base with warm accent
    COLORS = {
        # Base colors
        'background': '#fafafa',
        'surface': '#ffffff',
        'surface_elevated': '#ffffff',
        'surface_subtle': '#f8f9fa',
        
        # Text colors
        'text_primary': '#1a1a1a',
        'text_secondary': '#6b7280',
        'text_tertiary': '#9ca3af',
        'text_inverse': '#ffffff',
        
        # Accent colors
        'accent_primary': '#f59e0b',    # Warm amber
        'accent_secondary': '#fbbf24',  # Lighter amber
        'accent_subtle': '#fef3c7',     # Very light amber
        
        # Semantic colors
        'success': '#10b981',
        'success_subtle': '#d1fae5',
        'warning': '#f59e0b',
        'warning_subtle': '#fef3c7',
        'error': '#ef4444',
        'error_subtle': '#fee2e2',
        'info': '#3b82f6',
        'info_subtle': '#dbeafe',
        
        # Interactive states
        'hover': '#f3f4f6',
        'active': '#e5e7eb',
        'focus': '#f59e0b',
        'disabled': '#d1d5db',
        
        # Borders and dividers
        'border': '#e5e7eb',
        'border_subtle': '#f3f4f6',
        'divider': '#e5e7eb',
    }
    
    # Typography - Inter-inspired font stack
    FONTS = {
        'primary': ('Inter', 'SF Pro Display', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'),
        'mono': ('SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Consolas', 'monospace'),
    }
    
    # Font sizes and weights
    TYPOGRAPHY = {
        'display_large': {'size': 32, 'weight': 'bold', 'line_height': 1.2},
        'display_medium': {'size': 28, 'weight': 'bold', 'line_height': 1.25},
        'display_small': {'size': 24, 'weight': 'bold', 'line_height': 1.3},
        
        'headline_large': {'size': 20, 'weight': 'bold', 'line_height': 1.3},
        'headline_medium': {'size': 18, 'weight': 'bold', 'line_height': 1.35},
        'headline_small': {'size': 16, 'weight': 'bold', 'line_height': 1.4},
        
        'title_large': {'size': 15, 'weight': 'bold', 'line_height': 1.4},
        'title_medium': {'size': 14, 'weight': 'bold', 'line_height': 1.45},
        'title_small': {'size': 13, 'weight': 'bold', 'line_height': 1.5},
        
        'body_large': {'size': 14, 'weight': 'normal', 'line_height': 1.6},
        'body_medium': {'size': 13, 'weight': 'normal', 'line_height': 1.6},
        'body_small': {'size': 12, 'weight': 'normal', 'line_height': 1.6},
        
        'label_large': {'size': 12, 'weight': 'normal', 'line_height': 1.4},
        'label_medium': {'size': 11, 'weight': 'normal', 'line_height': 1.4},
        'label_small': {'size': 10, 'weight': 'normal', 'line_height': 1.4},
    }
    
    # Spacing system - 8px base unit
    SPACING = {
        'xs': 4,
        'sm': 8,
        'md': 16,
        'lg': 24,
        'xl': 32,
        'xxl': 48,
        'xxxl': 64,
    }
    
    @classmethod
    def get_font(cls, style: str) -> Tuple[str, int, str]:
        """Get font configuration for a typography style."""
        if style not in cls.TYPOGRAPHY:
            style = 'body_medium'
        
        config = cls.TYPOGRAPHY[style]
        font_family = cls.FONTS['primary'][0]  # Use first available font
        
        return (font_family, config['size'], config['weight'])
    
    @classmethod
    def create_card(cls, parent, **kwargs) -> tk.Frame:
        """Create a modern card component."""
        card = tk.Frame(
            parent,
            bg=cls.COLORS['surface'],
            relief='flat',
            bd=0,
            **kwargs
        )
        
        # Add subtle border effect
        card.configure(highlightbackground=cls.COLORS['border'], highlightthickness=1)
        
        return card
    
    @classmethod
    def create_button(cls, parent, text: str, style: str = 'primary', **kwargs) -> tk.Button:
        """Create a modern button component."""
        styles = {
            'primary': {
                'bg': cls.COLORS['accent_primary'],
                'fg': cls.COLORS['text_inverse'],
                'activebackground': cls.COLORS['accent_secondary'],
                'activeforeground': cls.COLORS['text_inverse'],
            },
            'secondary': {
                'bg': cls.COLORS['surface'],
                'fg': cls.COLORS['text_primary'],
                'activebackground': cls.COLORS['hover'],
                'activeforeground': cls.COLORS['text_primary'],
            },
            'ghost': {
                'bg': cls.COLORS['background'],
                'fg': cls.COLORS['text_secondary'],
                'activebackground': cls.COLORS['hover'],
                'activeforeground': cls.COLORS['text_primary'],
            }
        }
        
        style_config = styles.get(style, styles['primary'])
        
        button = tk.Button(
            parent,
            text=text,
            font=cls.get_font('label_medium'),
            relief='flat',
            bd=0,
            padx=cls.SPACING['md'],
            pady=cls.SPACING['sm'],
            cursor='hand2',
            **style_config,
            **kwargs
        )
        
        return button
    
    @classmethod
    def create_input(cls, parent, **kwargs) -> tk.Entry:
        """Create a modern input field."""
        entry = tk.Entry(
            parent,
            font=cls.get_font('body_medium'),
            bg=cls.COLORS['surface'],
            fg=cls.COLORS['text_primary'],
            relief='flat',
            bd=1,
            highlightthickness=1,
            highlightcolor=cls.COLORS['focus'],
            highlightbackground=cls.COLORS['border'],
            insertbackground=cls.COLORS['text_primary'],
            **kwargs
        )
        
        return entry
    
    @classmethod
    def create_label(cls, parent, text: str, style: str = 'body_medium', **kwargs) -> tk.Label:
        """Create a styled label."""
        label = tk.Label(
            parent,
            text=text,
            font=cls.get_font(style),
            bg=kwargs.get('bg', cls.COLORS['background']),
            fg=kwargs.get('fg', cls.COLORS['text_primary']),
            **{k: v for k, v in kwargs.items() if k not in ['bg', 'fg']}
        )
        
        return label
    
    @classmethod
    def create_section_header(cls, parent, title: str, subtitle: str = None) -> tk.Frame:
        """Create a section header with title and optional subtitle."""
        header_frame = tk.Frame(parent, bg=cls.COLORS['background'])
        
        title_label = cls.create_label(
            header_frame,
            title,
            style='headline_large',
            bg=cls.COLORS['background']
        )
        title_label.pack(anchor='w')
        
        if subtitle:
            subtitle_label = cls.create_label(
                header_frame,
                subtitle,
                style='body_medium',
                fg=cls.COLORS['text_secondary'],
                bg=cls.COLORS['background']
            )
            subtitle_label.pack(anchor='w', pady=(2, 0))
        
        return header_frame
    
    @classmethod
    def create_stats_card(cls, parent, value: str, label: str, color: str = 'accent_primary') -> tk.Frame:
        """Create a statistics card."""
        card = cls.create_card(parent)
        card.configure(padx=cls.SPACING['lg'], pady=cls.SPACING['lg'])
        
        # Value
        value_label = cls.create_label(
            card,
            value,
            style='display_small',
            fg=cls.COLORS[color],
            bg=cls.COLORS['surface']
        )
        value_label.pack()
        
        # Label
        label_widget = cls.create_label(
            card,
            label,
            style='label_medium',
            fg=cls.COLORS['text_secondary'],
            bg=cls.COLORS['surface']
        )
        label_widget.pack(pady=(4, 0))
        
        return card
    
    @classmethod
    def create_navigation_item(cls, parent, text: str, icon: str = "", active: bool = False, command: Callable = None) -> tk.Button:
        """Create a navigation item."""
        display_text = f"{icon} {text}" if icon else text
        
        bg_color = cls.COLORS['accent_subtle'] if active else cls.COLORS['surface']
        fg_color = cls.COLORS['accent_primary'] if active else cls.COLORS['text_secondary']
        
        nav_item = tk.Button(
            parent,
            text=display_text,
            font=cls.get_font('body_medium'),
            bg=bg_color,
            fg=fg_color,
            activebackground=cls.COLORS['hover'],
            activeforeground=cls.COLORS['text_primary'],
            relief='flat',
            bd=0,
            anchor='w',
            padx=cls.SPACING['md'],
            pady=cls.SPACING['sm'],
            cursor='hand2',
            command=command
        )
        
        return nav_item
    
    @classmethod
    def apply_hover_effect(cls, widget: tk.Widget, hover_bg: str = None, normal_bg: str = None):
        """Apply hover effects to a widget."""
        if hover_bg is None:
            hover_bg = cls.COLORS['hover']
        if normal_bg is None:
            normal_bg = widget.cget('bg')
        
        def on_enter(event):
            widget.configure(bg=hover_bg)
        
        def on_leave(event):
            widget.configure(bg=normal_bg)
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    @classmethod
    def create_divider(cls, parent, orientation: str = 'horizontal') -> tk.Frame:
        """Create a subtle divider."""
        if orientation == 'horizontal':
            divider = tk.Frame(
                parent,
                height=1,
                bg=cls.COLORS['divider'],
                relief='flat'
            )
        else:
            divider = tk.Frame(
                parent,
                width=1,
                bg=cls.COLORS['divider'],
                relief='flat'
            )
        
        return divider


class ModernScrollableFrame(tk.Frame):
    """A modern scrollable frame with custom styling."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(
            self,
            bg=DesignSystem.COLORS['background'],
            highlightthickness=0,
            relief='flat'
        )
        
        self.scrollbar = ttk.Scrollbar(
            self,
            orient='vertical',
            command=self.canvas.yview
        )
        
        self.scrollable_frame = tk.Frame(
            self.canvas,
            bg=DesignSystem.COLORS['background']
        )
        
        # Configure scrolling
        self.scrollable_frame.bind(
            '<Configure>',
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack elements
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        
        # Bind mousewheel
        self._bind_mousewheel()
    
    def _bind_mousewheel(self):
        """Bind mousewheel scrolling."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        
        self.canvas.bind('<MouseWheel>', _on_mousewheel)
        self.scrollable_frame.bind('<MouseWheel>', _on_mousewheel)