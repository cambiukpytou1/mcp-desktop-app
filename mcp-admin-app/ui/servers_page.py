"""
Servers Management Page
=======================

UI page for managing MCP servers with enhanced monitoring and controls.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from typing import Optional, List
from datetime import datetime

from models.server import MCPServer
from models.base import ServerStatus


class ServersPage(tk.Frame):
    """Enhanced servers management page."""
    
    def __init__(self, parent, server_manager, monitoring_service):
        super().__init__(parent, bg="#f9f9f9")
        self.server_manager = server_manager
        self.monitoring_service = monitoring_service
        self.logger = logging.getLogger(__name__)
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create page widgets."""
        # Header
        header_frame = tk.Frame(self, bg="#f9f9f9")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(
            header_frame,
            text="MCP Server Administration",
            font=("Arial", 20, "bold"),
            bg="#f9f9f9"
        ).pack(side="left")
        
        # Add server button
        tk.Button(
            header_frame,
            text="+ Add Server",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self._add_server_dialog
        ).pack(side="right")
        
        # Summary cards
        self._create_summary_cards()
        
        # Servers list
        self._create_servers_list()
    
    def _create_summary_cards(self):
        """Create summary statistics cards."""
        cards_frame = tk.Frame(self, bg="#f9f9f9")
        cards_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Get server statistics
        servers = self.server_manager.get_all_servers()
        total_servers = len(servers)
        running_servers = len([s for s in servers if s.status == ServerStatus.RUNNING])
        stopped_servers = len([s for s in servers if s.status == ServerStatus.STOPPED])
        error_servers = len([s for s in servers if s.status == ServerStatus.ERROR])
        
        # Create cards
        self._create_card(cards_frame, str(total_servers), "Total Servers", "#ffffff")
        self._create_card(cards_frame, str(running_servers), "Running", "#e8f5e8", "#34a853")
        self._create_card(cards_frame, str(stopped_servers), "Stopped", "#fff3e0", "#ff9800")
        self._create_card(cards_frame, str(error_servers), "Errors", "#ffebee", "#f44336")
    
    def _create_card(self, parent, value, label, bg_color, text_color="#1a73e8"):
        """Create a summary card."""
        card = tk.Frame(parent, bg=bg_color, bd=1, relief="solid")
        card.pack(side="left", padx=10, ipadx=20, ipady=15, expand=True, fill="both")
        
        tk.Label(
            card,
            text=value,
            font=("Arial", 24, "bold"),
            fg=text_color,
            bg=bg_color
        ).pack()
        
        tk.Label(
            card,
            text=label,
            font=("Arial", 11),
            fg="#666",
            bg=bg_color
        ).pack()
    
    def _create_servers_list(self):
        """Create servers list with controls."""
        # List header
        list_header = tk.Frame(self, bg="#f9f9f9")
        list_header.pack(fill="x", padx=20, pady=(0, 10))
        
        tk.Label(
            list_header,
            text="Servers",
            font=("Arial", 16, "bold"),
            bg="#f9f9f9"
        ).pack(side="left")
        
        # Refresh button
        tk.Button(
            list_header,
            text="🔄 Refresh",
            bg="#f8f9fa",
            fg="#333",
            font=("Arial", 9),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self.refresh
        ).pack(side="right")
        
        # Servers container with scrollbar
        container_frame = tk.Frame(self, bg="#f9f9f9")
        container_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Create scrollable frame
        canvas = tk.Canvas(container_frame, bg="#f9f9f9", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
        self.servers_frame = tk.Frame(canvas, bg="#f9f9f9")
        
        self.servers_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.servers_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_server_row(self, server: MCPServer):
        """Create a server row widget."""
        row = tk.Frame(self.servers_frame, bg="#ffffff", bd=1, relief="solid")
        row.pack(fill="x", pady=4)
        
        # Server info section
        info_frame = tk.Frame(row, bg="#ffffff")
        info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=12)
        
        # Server name and status
        name_frame = tk.Frame(info_frame, bg="#ffffff")
        name_frame.pack(fill="x")
        
        tk.Label(
            name_frame,
            text=server.name,
            font=("Arial", 14, "bold"),
            bg="#ffffff"
        ).pack(side="left")
        
        # Status indicator
        status_colors = {
            ServerStatus.RUNNING: "#34a853",
            ServerStatus.STOPPED: "#9e9e9e",
            ServerStatus.ERROR: "#d93025",
            ServerStatus.UNKNOWN: "#ff9800"
        }
        
        status_color = status_colors.get(server.status, "#9e9e9e")
        status_label = tk.Label(
            name_frame,
            text=server.status.value.title(),
            font=("Arial", 9, "bold"),
            fg="white",
            bg=status_color,
            padx=8,
            pady=2
        )
        status_label.pack(side="left", padx=(10, 0))
        
        # Server details
        details_frame = tk.Frame(info_frame, bg="#ffffff")
        details_frame.pack(fill="x", pady=(5, 0))
        
        # Command
        tk.Label(
            details_frame,
            text=f"Command: {server.command}",
            font=("Arial", 10),
            fg="#666",
            bg="#ffffff"
        ).pack(anchor="w")
        
        # Last seen
        last_seen = server.last_seen.strftime("%Y-%m-%d %H:%M:%S") if server.last_seen else "Never"
        tk.Label(
            details_frame,
            text=f"Last seen: {last_seen}",
            font=("Arial", 10),
            fg="#666",
            bg="#ffffff"
        ).pack(anchor="w")
        
        # Actions section
        actions_frame = tk.Frame(row, bg="#ffffff")
        actions_frame.pack(side="right", padx=15, pady=12)
        
        # Action buttons based on status
        if server.status == ServerStatus.RUNNING:
            tk.Button(
                actions_frame,
                text="Stop",
                bg="#d93025",
                fg="white",
                font=("Arial", 9, "bold"),
                padx=12,
                pady=6,
                relief="flat",
                cursor="hand2",
                command=lambda: self._stop_server(server.id)
            ).pack(side="left", padx=2)
            
            tk.Button(
                actions_frame,
                text="Restart",
                bg="#ff9800",
                fg="white",
                font=("Arial", 9, "bold"),
                padx=12,
                pady=6,
                relief="flat",
                cursor="hand2",
                command=lambda: self._restart_server(server.id)
            ).pack(side="left", padx=2)
        else:
            tk.Button(
                actions_frame,
                text="Start",
                bg="#34a853",
                fg="white",
                font=("Arial", 9, "bold"),
                padx=12,
                pady=6,
                relief="flat",
                cursor="hand2",
                command=lambda: self._start_server(server.id)
            ).pack(side="left", padx=2)
        
        # Edit button
        tk.Button(
            actions_frame,
            text="Edit",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=lambda: self._edit_server(server.id)
        ).pack(side="left", padx=2)
        
        # Delete button
        tk.Button(
            actions_frame,
            text="Delete",
            bg="#666",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=lambda: self._delete_server(server.id)
        ).pack(side="left", padx=2)
    
    def refresh(self):
        """Refresh the servers list."""
        try:
            # Clear existing server rows
            for widget in self.servers_frame.winfo_children():
                widget.destroy()
            
            # Get updated server list
            servers = self.server_manager.get_all_servers()
            
            if not servers:
                # Show empty state
                empty_frame = tk.Frame(self.servers_frame, bg="#f9f9f9")
                empty_frame.pack(fill="both", expand=True, pady=50)
                
                tk.Label(
                    empty_frame,
                    text="No servers configured",
                    font=("Arial", 14),
                    fg="#666",
                    bg="#f9f9f9"
                ).pack()
                
                tk.Label(
                    empty_frame,
                    text="Click 'Add Server' to get started",
                    font=("Arial", 11),
                    fg="#999",
                    bg="#f9f9f9"
                ).pack(pady=(5, 0))
            else:
                # Create server rows
                for server in servers:
                    self._create_server_row(server)
            
            self.logger.debug(f"Refreshed servers page with {len(servers)} servers")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh servers page: {e}")
            messagebox.showerror("Error", f"Failed to refresh servers: {e}")
    
    def _add_server_dialog(self):
        """Show add server dialog."""
        dialog = AddServerDialog(self)
        if dialog.result:
            try:
                server = self.server_manager.add_server(
                    name=dialog.result["name"],
                    command=dialog.result["command"],
                    args=dialog.result["args"],
                    env=dialog.result["env"],
                    description=dialog.result["description"]
                )
                self.refresh()
                messagebox.showinfo("Success", f"Server '{server.name}' added successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add server: {e}")
    
    def _start_server(self, server_id: str):
        """Start a server."""
        try:
            if self.server_manager.start_server(server_id):
                self.refresh()
                messagebox.showinfo("Success", "Server started successfully")
            else:
                messagebox.showerror("Error", "Failed to start server")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
    
    def _stop_server(self, server_id: str):
        """Stop a server."""
        try:
            if self.server_manager.stop_server(server_id):
                self.refresh()
                messagebox.showinfo("Success", "Server stopped successfully")
            else:
                messagebox.showerror("Error", "Failed to stop server")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop server: {e}")
    
    def _restart_server(self, server_id: str):
        """Restart a server."""
        try:
            if self.server_manager.restart_server(server_id):
                self.refresh()
                messagebox.showinfo("Success", "Server restarted successfully")
            else:
                messagebox.showerror("Error", "Failed to restart server")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart server: {e}")
    
    def _edit_server(self, server_id: str):
        """Edit a server configuration."""
        server = self.server_manager.get_server(server_id)
        if not server:
            messagebox.showerror("Error", "Server not found")
            return
        
        dialog = EditServerDialog(self, server)
        if dialog.result:
            try:
                self.server_manager.update_server(server_id, **dialog.result)
                self.refresh()
                messagebox.showinfo("Success", "Server updated successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update server: {e}")
    
    def _delete_server(self, server_id: str):
        """Delete a server."""
        server = self.server_manager.get_server(server_id)
        if not server:
            return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete server '{server.name}'?"):
            try:
                if self.server_manager.remove_server(server_id):
                    self.refresh()
                    messagebox.showinfo("Success", "Server deleted successfully")
                else:
                    messagebox.showerror("Error", "Failed to delete server")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete server: {e}")


class AddServerDialog:
    """Dialog for adding a new server."""
    
    def __init__(self, parent):
        self.result = None
        self._create_dialog(parent)
    
    def _create_dialog(self, parent):
        """Create the dialog window."""
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add New Server")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Create form
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Name field
        tk.Label(main_frame, text="Server Name:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.name_entry = tk.Entry(main_frame, font=("Arial", 11))
        self.name_entry.pack(fill="x", pady=(5, 15))
        
        # Command field
        tk.Label(main_frame, text="Command:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.command_entry = tk.Entry(main_frame, font=("Arial", 11))
        self.command_entry.pack(fill="x", pady=(5, 15))
        
        # Arguments field
        tk.Label(main_frame, text="Arguments (one per line):", font=("Arial", 11, "bold")).pack(anchor="w")
        self.args_text = tk.Text(main_frame, height=4, font=("Arial", 10))
        self.args_text.pack(fill="x", pady=(5, 15))
        
        # Description field
        tk.Label(main_frame, text="Description:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.description_entry = tk.Entry(main_frame, font=("Arial", 11))
        self.description_entry.pack(fill="x", pady=(5, 15))
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy,
            padx=20,
            pady=8
        ).pack(side="right", padx=(10, 0))
        
        tk.Button(
            button_frame,
            text="Add Server",
            command=self._add_server,
            bg="#1a73e8",
            fg="white",
            padx=20,
            pady=8
        ).pack(side="right")
        
        # Focus on name field
        self.name_entry.focus()
    
    def _add_server(self):
        """Process the add server request."""
        name = self.name_entry.get().strip()
        command = self.command_entry.get().strip()
        args_text = self.args_text.get("1.0", tk.END).strip()
        description = self.description_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Server name is required")
            return
        
        if not command:
            messagebox.showerror("Error", "Command is required")
            return
        
        # Parse arguments
        args = [arg.strip() for arg in args_text.split('\n') if arg.strip()] if args_text else []
        
        self.result = {
            "name": name,
            "command": command,
            "args": args,
            "env": {},  # Could add env variable support later
            "description": description
        }
        
        self.dialog.destroy()


class EditServerDialog:
    """Dialog for editing server configuration."""
    
    def __init__(self, parent, server: MCPServer):
        self.server = server
        self.result = None
        self._create_dialog(parent)
    
    def _create_dialog(self, parent):
        """Create the dialog window."""
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Edit Server: {self.server.name}")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Create form
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Name field
        tk.Label(main_frame, text="Server Name:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.name_entry = tk.Entry(main_frame, font=("Arial", 11))
        self.name_entry.pack(fill="x", pady=(5, 15))
        self.name_entry.insert(0, self.server.name)
        
        # Command field
        tk.Label(main_frame, text="Command:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.command_entry = tk.Entry(main_frame, font=("Arial", 11))
        self.command_entry.pack(fill="x", pady=(5, 15))
        self.command_entry.insert(0, self.server.command)
        
        # Arguments field
        tk.Label(main_frame, text="Arguments (one per line):", font=("Arial", 11, "bold")).pack(anchor="w")
        self.args_text = tk.Text(main_frame, height=4, font=("Arial", 10))
        self.args_text.pack(fill="x", pady=(5, 15))
        if self.server.args:
            self.args_text.insert("1.0", '\n'.join(self.server.args))
        
        # Description field
        tk.Label(main_frame, text="Description:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.description_entry = tk.Entry(main_frame, font=("Arial", 11))
        self.description_entry.pack(fill="x", pady=(5, 15))
        self.description_entry.insert(0, self.server.description)
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy,
            padx=20,
            pady=8
        ).pack(side="right", padx=(10, 0))
        
        tk.Button(
            button_frame,
            text="Save Changes",
            command=self._save_changes,
            bg="#1a73e8",
            fg="white",
            padx=20,
            pady=8
        ).pack(side="right")
    
    def _save_changes(self):
        """Process the save changes request."""
        name = self.name_entry.get().strip()
        command = self.command_entry.get().strip()
        args_text = self.args_text.get("1.0", tk.END).strip()
        description = self.description_entry.get().strip()
        
        if not name:
            messagebox.showerror("Error", "Server name is required")
            return
        
        if not command:
            messagebox.showerror("Error", "Command is required")
            return
        
        # Parse arguments
        args = [arg.strip() for arg in args_text.split('\n') if arg.strip()] if args_text else []
        
        self.result = {
            "name": name,
            "command": command,
            "args": args,
            "description": description
        }
        
        self.dialog.destroy()