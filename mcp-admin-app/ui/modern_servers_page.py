"""
Modern Servers Management Page
==============================

A redesigned servers management page using the modern design system
with Substack-inspired aesthetics.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from typing import Optional, List
from datetime import datetime

from models.server import MCPServer
from models.base import ServerStatus
from ui.design_system import DesignSystem, ModernScrollableFrame


class ModernServersPage(tk.Frame):
    """Modern servers management page with contemporary design."""
    
    def __init__(self, parent, server_manager, monitoring_service):
        super().__init__(parent, bg=DesignSystem.COLORS['background'])
        self.server_manager = server_manager
        self.monitoring_service = monitoring_service
        self.logger = logging.getLogger(__name__)
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create page widgets with modern design."""
        # Main container with padding
        self.main_container = tk.Frame(self, bg=DesignSystem.COLORS['background'])
        self.main_container.pack(fill="both", expand=True, padx=DesignSystem.SPACING['xl'], pady=DesignSystem.SPACING['xl'])
        
        # Header section
        self._create_header(self.main_container)
        
        # Stats dashboard
        self.stats_frame = tk.Frame(self.main_container, bg=DesignSystem.COLORS['background'])
        self.stats_frame.pack(fill="x", pady=(0, DesignSystem.SPACING['xl']))
        self._create_stats_dashboard(self.stats_frame)
        
        # Servers list
        self._create_servers_list(self.main_container)
    
    def _create_header(self, parent):
        """Create modern page header."""
        header_frame = tk.Frame(parent, bg=DesignSystem.COLORS['background'])
        header_frame.pack(fill="x", pady=(0, DesignSystem.SPACING['xl']))
        
        # Title section
        title_section = DesignSystem.create_section_header(
            header_frame,
            "Server Management",
            "Manage and monitor your MCP servers"
        )
        title_section.pack(side="left", fill="x", expand=True)
        
        # Action buttons
        actions_frame = tk.Frame(header_frame, bg=DesignSystem.COLORS['background'])
        actions_frame.pack(side="right")
        
        # Add server button
        add_btn = DesignSystem.create_button(
            actions_frame,
            "Add Server",
            style='primary',
            command=self._add_server_dialog
        )
        add_btn.pack(side="left", padx=(0, DesignSystem.SPACING['sm']))
        
        # Refresh button
        refresh_btn = DesignSystem.create_button(
            actions_frame,
            "Refresh",
            style='secondary',
            command=self.refresh
        )
        refresh_btn.pack(side="left")
    
    def _create_stats_dashboard(self, parent):
        """Create modern statistics dashboard."""
        # Clear existing stats
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Get server statistics
        servers = self.server_manager.get_all_servers()
        total_servers = len(servers)
        running_servers = len([s for s in servers if s.status == ServerStatus.RUNNING])
        stopped_servers = len([s for s in servers if s.status == ServerStatus.STOPPED])
        error_servers = len([s for s in servers if s.status == ServerStatus.ERROR])
        
        # Create stats cards
        stats_container = tk.Frame(parent, bg=DesignSystem.COLORS['background'])
        stats_container.pack(fill="x")
        
        # Total servers card
        total_card = DesignSystem.create_stats_card(
            stats_container,
            str(total_servers),
            "Total Servers",
            'text_primary'
        )
        total_card.pack(side="left", fill="both", expand=True, padx=(0, DesignSystem.SPACING['md']))
        
        # Running servers card
        running_card = DesignSystem.create_stats_card(
            stats_container,
            str(running_servers),
            "Running",
            'success'
        )
        running_card.pack(side="left", fill="both", expand=True, padx=(0, DesignSystem.SPACING['md']))
        
        # Stopped servers card
        stopped_card = DesignSystem.create_stats_card(
            stats_container,
            str(stopped_servers),
            "Stopped",
            'warning'
        )
        stopped_card.pack(side="left", fill="both", expand=True, padx=(0, DesignSystem.SPACING['md']))
        
        # Error servers card
        error_card = DesignSystem.create_stats_card(
            stats_container,
            str(error_servers),
            "Errors",
            'error'
        )
        error_card.pack(side="left", fill="both", expand=True)
    
    def _create_servers_list(self, parent):
        """Create modern servers list."""
        # List container
        list_container = tk.Frame(parent, bg=DesignSystem.COLORS['background'])
        list_container.pack(fill="both", expand=True)
        
        # Section header
        list_header = tk.Frame(list_container, bg=DesignSystem.COLORS['background'])
        list_header.pack(fill="x", pady=(0, DesignSystem.SPACING['md']))
        
        DesignSystem.create_label(
            list_header,
            "Active Servers",
            style='title_large',
            bg=DesignSystem.COLORS['background']
        ).pack(side="left")
        
        # Servers list with modern cards
        self.servers_frame = ModernScrollableFrame(list_container)
        self.servers_frame.pack(fill="both", expand=True)
        
        # Initially populate with placeholder
        self._populate_servers_list()
    
    def _populate_servers_list(self):
        """Populate the servers list with modern server cards."""
        # Clear existing widgets
        for widget in self.servers_frame.scrollable_frame.winfo_children():
            widget.destroy()
        
        servers = self.server_manager.get_all_servers()
        
        if not servers:
            # Empty state
            empty_state = self._create_empty_state(self.servers_frame.scrollable_frame)
            empty_state.pack(fill="both", expand=True, pady=DesignSystem.SPACING['xl'])
        else:
            # Server cards
            for server in servers:
                server_card = self._create_server_card(self.servers_frame.scrollable_frame, server)
                server_card.pack(fill="x", pady=(0, DesignSystem.SPACING['md']))
    
    def _create_server_card(self, parent, server: MCPServer) -> tk.Frame:
        """Create a modern server card."""
        card = DesignSystem.create_card(parent)
        card.configure(padx=DesignSystem.SPACING['lg'], pady=DesignSystem.SPACING['lg'])
        
        # Header row
        header_row = tk.Frame(card, bg=DesignSystem.COLORS['surface'])
        header_row.pack(fill="x", pady=(0, DesignSystem.SPACING['sm']))
        
        # Server name and status
        name_status_frame = tk.Frame(header_row, bg=DesignSystem.COLORS['surface'])
        name_status_frame.pack(side="left", fill="x", expand=True)
        
        # Server name
        DesignSystem.create_label(
            name_status_frame,
            server.name,
            style='title_medium',
            bg=DesignSystem.COLORS['surface']
        ).pack(anchor="w")
        
        # Status indicator
        status_frame = tk.Frame(name_status_frame, bg=DesignSystem.COLORS['surface'])
        status_frame.pack(anchor="w", pady=(2, 0))
        
        status_colors = {
            ServerStatus.RUNNING: DesignSystem.COLORS['success'],
            ServerStatus.STOPPED: DesignSystem.COLORS['text_secondary'],
            ServerStatus.ERROR: DesignSystem.COLORS['error'],
            ServerStatus.UNKNOWN: DesignSystem.COLORS['warning'],
        }
        
        status_color = status_colors.get(server.status, DesignSystem.COLORS['text_secondary'])
        status_text = f"● {server.status.value.title()}"
        
        DesignSystem.create_label(
            status_frame,
            status_text,
            style='label_small',
            fg=status_color,
            bg=DesignSystem.COLORS['surface']
        ).pack(side="left")
        
        # Actions
        actions_frame = tk.Frame(header_row, bg=DesignSystem.COLORS['surface'])
        actions_frame.pack(side="right")
        
        # Start/Stop button
        if server.status == ServerStatus.RUNNING:
            action_btn = DesignSystem.create_button(
                actions_frame,
                "Stop",
                style='ghost',
                command=lambda: self._stop_server(server)
            )
        else:
            action_btn = DesignSystem.create_button(
                actions_frame,
                "Start",
                style='primary',
                command=lambda: self._start_server(server)
            )
        
        action_btn.pack(side="left", padx=(0, DesignSystem.SPACING['sm']))
        
        # More actions button
        more_btn = DesignSystem.create_button(
            actions_frame,
            "⋯",
            style='ghost',
            command=lambda: self._show_server_menu(server)
        )
        more_btn.pack(side="left")
        
        # Details row
        if server.command or server.args:
            details_row = tk.Frame(card, bg=DesignSystem.COLORS['surface'])
            details_row.pack(fill="x", pady=(DesignSystem.SPACING['sm'], 0))
            
            # Command details
            command_text = f"{server.command} {' '.join(server.args) if server.args else ''}"
            if len(command_text) > 80:
                command_text = command_text[:77] + "..."
            
            DesignSystem.create_label(
                details_row,
                command_text,
                style='body_small',
                fg=DesignSystem.COLORS['text_secondary'],
                bg=DesignSystem.COLORS['surface']
            ).pack(anchor="w")
        
        # Add hover effect
        DesignSystem.apply_hover_effect(card, DesignSystem.COLORS['surface_subtle'])
        
        return card
    
    def _create_empty_state(self, parent) -> tk.Frame:
        """Create empty state when no servers exist."""
        empty_frame = tk.Frame(parent, bg=DesignSystem.COLORS['background'])
        
        # Empty state card
        empty_card = DesignSystem.create_card(empty_frame)
        empty_card.pack(expand=True, padx=DesignSystem.SPACING['xl'], pady=DesignSystem.SPACING['xl'])
        empty_card.configure(padx=DesignSystem.SPACING['xxl'], pady=DesignSystem.SPACING['xxl'])
        
        # Icon
        DesignSystem.create_label(
            empty_card,
            "⚡",
            style='display_large',
            fg=DesignSystem.COLORS['text_tertiary'],
            bg=DesignSystem.COLORS['surface']
        ).pack(pady=(0, DesignSystem.SPACING['md']))
        
        # Title
        DesignSystem.create_label(
            empty_card,
            "No servers configured",
            style='headline_medium',
            bg=DesignSystem.COLORS['surface']
        ).pack(pady=(0, DesignSystem.SPACING['sm']))
        
        # Description
        DesignSystem.create_label(
            empty_card,
            "Get started by adding your first MCP server",
            style='body_medium',
            fg=DesignSystem.COLORS['text_secondary'],
            bg=DesignSystem.COLORS['surface']
        ).pack(pady=(0, DesignSystem.SPACING['lg']))
        
        # Add server button
        add_btn = DesignSystem.create_button(
            empty_card,
            "Add Your First Server",
            style='primary',
            command=self._add_server_dialog
        )
        add_btn.pack()
        
        return empty_frame
    
    def _add_server_dialog(self):
        """Show add server dialog."""
        # Create modern dialog
        dialog = tk.Toplevel(self)
        dialog.title("Add New Server")
        dialog.geometry("500x400")
        dialog.configure(bg=DesignSystem.COLORS['background'])
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"500x400+{x}+{y}")
        
        # Dialog content
        content = tk.Frame(dialog, bg=DesignSystem.COLORS['background'])
        content.pack(fill="both", expand=True, padx=DesignSystem.SPACING['xl'], pady=DesignSystem.SPACING['xl'])
        
        # Header
        header = DesignSystem.create_section_header(
            content,
            "Add New Server",
            "Configure a new MCP server"
        )
        header.pack(fill="x", pady=(0, DesignSystem.SPACING['lg']))
        
        # Form fields
        form_frame = tk.Frame(content, bg=DesignSystem.COLORS['background'])
        form_frame.pack(fill="both", expand=True)
        
        # Server name
        DesignSystem.create_label(
            form_frame,
            "Server Name",
            style='label_medium',
            bg=DesignSystem.COLORS['background']
        ).pack(anchor="w", pady=(0, DesignSystem.SPACING['xs']))
        
        name_entry = DesignSystem.create_input(form_frame)
        name_entry.pack(fill="x", pady=(0, DesignSystem.SPACING['md']))
        name_entry.focus()
        
        # Command
        DesignSystem.create_label(
            form_frame,
            "Command",
            style='label_medium',
            bg=DesignSystem.COLORS['background']
        ).pack(anchor="w", pady=(0, DesignSystem.SPACING['xs']))
        
        command_entry = DesignSystem.create_input(form_frame)
        command_entry.pack(fill="x", pady=(0, DesignSystem.SPACING['md']))
        
        # Arguments
        DesignSystem.create_label(
            form_frame,
            "Arguments (optional)",
            style='label_medium',
            bg=DesignSystem.COLORS['background']
        ).pack(anchor="w", pady=(0, DesignSystem.SPACING['xs']))
        
        args_entry = DesignSystem.create_input(form_frame)
        args_entry.pack(fill="x", pady=(0, DesignSystem.SPACING['lg']))
        
        # Buttons
        buttons_frame = tk.Frame(content, bg=DesignSystem.COLORS['background'])
        buttons_frame.pack(fill="x", pady=(DesignSystem.SPACING['lg'], 0))
        
        def save_server():
            name = name_entry.get().strip()
            command = command_entry.get().strip()
            args = args_entry.get().strip().split() if args_entry.get().strip() else []
            
            if not name or not command:
                messagebox.showerror("Error", "Name and command are required")
                return
            
            try:
                server = MCPServer(
                    name=name,
                    command=command,
                    args=args,
                    status=ServerStatus.STOPPED
                )
                self.server_manager.add_server(server)
                dialog.destroy()
                self.refresh()
                messagebox.showinfo("Success", f"Server '{name}' added successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add server: {e}")
        
        # Save button
        save_btn = DesignSystem.create_button(
            buttons_frame,
            "Add Server",
            style='primary',
            command=save_server
        )
        save_btn.pack(side="right")
        
        # Cancel button
        cancel_btn = DesignSystem.create_button(
            buttons_frame,
            "Cancel",
            style='secondary',
            command=dialog.destroy
        )
        cancel_btn.pack(side="right", padx=(0, DesignSystem.SPACING['sm']))
    
    def _start_server(self, server: MCPServer):
        """Start a server."""
        try:
            self.server_manager.start_server(server.name)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
    
    def _stop_server(self, server: MCPServer):
        """Stop a server."""
        try:
            self.server_manager.stop_server(server.name)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")
    
    def _show_server_menu(self, server: MCPServer):
        """Show server context menu."""
        # Simple implementation - could be enhanced with a proper context menu
        actions = ["Edit", "Delete", "View Logs", "Restart"]
        action = simpledialog.askstring(
            "Server Actions",
            f"Available actions for {server.name}:\n" + "\n".join(f"{i+1}. {action}" for i, action in enumerate(actions)) + "\n\nEnter action number:"
        )
        
        if action == "1":  # Edit
            self._edit_server(server)
        elif action == "2":  # Delete
            self._delete_server(server)
        elif action == "3":  # View Logs
            self._view_server_logs(server)
        elif action == "4":  # Restart
            self._restart_server(server)
    
    def _edit_server(self, server: MCPServer):
        """Edit server configuration."""
        messagebox.showinfo("Edit Server", f"Edit functionality for {server.name} would be implemented here")
    
    def _delete_server(self, server: MCPServer):
        """Delete a server."""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete server '{server.name}'?"):
            try:
                self.server_manager.remove_server(server.name)
                self.refresh()
                messagebox.showinfo("Success", f"Server '{server.name}' deleted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete server: {e}")
    
    def _view_server_logs(self, server: MCPServer):
        """View server logs."""
        messagebox.showinfo("Server Logs", f"Log viewer for {server.name} would be implemented here")
    
    def _restart_server(self, server: MCPServer):
        """Restart a server."""
        try:
            if server.status == ServerStatus.RUNNING:
                self.server_manager.stop_server(server.name)
            self.server_manager.start_server(server.name)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart server: {e}")
    
    def refresh(self):
        """Refresh the page data."""
        try:
            # Refresh stats dashboard
            if hasattr(self, 'stats_frame'):
                self._create_stats_dashboard(self.stats_frame)
            
            # Refresh servers list
            self._populate_servers_list()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh servers page: {e}")