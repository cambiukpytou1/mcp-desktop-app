"""
MCP Desktop Administration Client
================================

This script implements a simple cross‑platform desktop user interface for
administering MCP servers, tools, context resources, prompts, security and
system logs. It relies on the built‑in ``tkinter`` library, so no external
dependencies are required. The application replicates the major features
exposed in the web prototype via a resizable window with a persistent
navigation sidebar and distinct content panels.

Usage:

```
python mcp_desktop.py
```

The application is a prototype and does not persist data; buttons and
actions are placeholders intended to illustrate layout and flow. To
integrate with an actual back‑end, hook the button callbacks into your
MCP server API.
"""

import tkinter as tk
from tkinter import ttk


class MCPAdminApp(tk.Tk):
    """Main application window for the MCP desktop client."""

    def __init__(self):
        super().__init__()
        self.title("MCP Admin")
        # Define a fixed size window. Feel free to adjust or make resizable.
        self.geometry("1000x650")
        self.configure(bg="#f9f9f9")

        # Create navigation sidebar and content container
        self.sidebar = tk.Frame(self, width=200, bg="white", bd=0, relief="flat")
        self.sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(self, bg="#f9f9f9")
        self.content.pack(side="right", fill="both", expand=True)

        # Dictionary mapping page names to their frames
        self.pages = {}

        # Build all pages
        self.pages["servers"] = self._create_servers_page()
        self.pages["tools"] = self._create_tools_page()
        self.pages["context"] = self._create_context_page()
        self.pages["prompts"] = self._create_prompts_page()
        self.pages["security"] = self._create_security_page()
        self.pages["logs"] = self._create_logs_page()

        # Create navigation buttons
        nav_items = [
            ("Servers", "servers"),
            ("Tools", "tools"),
            ("Context", "context"),
            ("Prompts", "prompts"),
            ("Security", "security"),
            ("Logs", "logs"),
        ]

        for label, key in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=label,
                anchor="w",
                padx=20,
                pady=10,
                relief="flat",
                bg="white",
                fg="#333",
                activebackground="#e8f0fe",
                activeforeground="#1a73e8",
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x")

        # Initially show the servers page
        self.show_page("servers")

    def show_page(self, key: str) -> None:
        """Display the selected page and hide others."""
        for page_key, frame in self.pages.items():
            if page_key == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    # Helper methods to build each page
    def _create_servers_page(self) -> tk.Frame:
        frame = tk.Frame(self.content, bg="#f9f9f9")

        # Heading
        tk.Label(frame, text="MCP Server Administration", font=("Arial", 20, "bold"), bg="#f9f9f9").pack(anchor="w", padx=20, pady=(20, 10))

        # Summary cards
        cards_container = tk.Frame(frame, bg="#f9f9f9")
        cards_container.pack(fill="x", padx=20, pady=(0, 20))

        def create_card(parent, value, label, color="#ffffff"):
            card = tk.Frame(parent, bg=color, bd=1, relief="solid", highlightthickness=0)
            card.pack(side="left", padx=10, ipadx=20, ipady=15, expand=True, fill="both")
            tk.Label(card, text=value, font=("Arial", 26, "bold"), fg="#1a73e8", bg=color).pack()
            tk.Label(card, text=label, font=("Arial", 12), fg="#666", bg=color).pack()
            return card

        create_card(cards_container, "3", "Total servers")
        create_card(cards_container, "5", "Total tools")
        # Action card for adding server
        add_card = tk.Frame(cards_container, bg="#ffffff", bd=1, relief="solid")
        add_card.pack(side="left", padx=10, ipadx=20, ipady=15, expand=True, fill="both")
        btn = tk.Button(add_card, text="+ Add new server", fg="#1a73e8", bg="#ffffff", borderwidth=0)
        btn.pack(expand=True)

        # Server list heading
        tk.Label(frame, text="Servers", font=("Arial", 16, "bold"), bg="#f9f9f9").pack(anchor="w", padx=20, pady=(0, 10))

        # List of servers
        servers_container = tk.Frame(frame, bg="#f9f9f9")
        servers_container.pack(fill="both", padx=20)

        # Sample servers data
        server_data = [
            {"name": "server-1", "status": "Running"},
            {"name": "server-2", "status": "Stopped"},
            {"name": "server-3", "status": "Running"},
        ]

        for srv in server_data:
            row = tk.Frame(servers_container, bg="#ffffff", bd=1, relief="solid")
            row.pack(fill="x", pady=4)
            # Name and status
            left = tk.Frame(row, bg="#ffffff")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            tk.Label(left, text=srv["name"], font=("Arial", 14, "bold"), bg="#ffffff").pack(anchor="w")
            status_color = "#34a853" if srv["status"].lower() == "running" else "#9e9e9e"
            status_label = tk.Label(left, text=srv["status"], font=("Arial", 10), fg="#ffffff", bg=status_color, padx=10, pady=2)
            status_label.pack(anchor="w", pady=2)
            # Actions
            right = tk.Frame(row, bg="#ffffff")
            right.pack(side="right", padx=10, pady=10)
            if srv["status"].lower() == "running":
                action_btn = tk.Button(right, text="Stop", bg="#d93025", fg="white", padx=10)
            else:
                action_btn = tk.Button(right, text="Start", bg="#34a853", fg="white", padx=10)
            action_btn.pack(side="left", padx=4)
            tk.Button(right, text="?", bg="#e0e0e0", fg="#333", padx=10).pack(side="left", padx=4)

        return frame

    def _create_tools_page(self) -> tk.Frame:
        frame = tk.Frame(self.content, bg="#f9f9f9")
        tk.Label(frame, text="Manage Tools", font=("Arial", 20, "bold"), bg="#f9f9f9").pack(anchor="w", padx=20, pady=(20, 10))
        # Add new tool button
        tk.Button(frame, text="+ Add new tool", bg="#1a73e8", fg="#fff", padx=12, pady=6, borderwidth=0).pack(anchor="w", padx=20, pady=(0, 20))
        # Tools list
        tools_container = tk.Frame(frame, bg="#f9f9f9")
        tools_container.pack(fill="both", padx=20)
        tools_data = [
            {"name": "Tool A", "desc": "Description of Tool A"},
            {"name": "Tool B", "desc": "Description of Tool B"},
            {"name": "Tool C", "desc": "Description of Tool C"},
        ]
        for tool in tools_data:
            row = tk.Frame(tools_container, bg="#ffffff", bd=1, relief="solid")
            row.pack(fill="x", pady=4)
            # Tool details
            left = tk.Frame(row, bg="#ffffff")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            tk.Label(left, text=tool["name"], font=("Arial", 14, "bold"), bg="#ffffff").pack(anchor="w")
            tk.Label(left, text=tool["desc"], font=("Arial", 10), fg="#666", bg="#ffffff").pack(anchor="w")
            # Actions
            right = tk.Frame(row, bg="#ffffff")
            right.pack(side="right", padx=10, pady=10)
            tk.Button(right, text="Edit", bg="#fbbc04", fg="#333", padx=10).pack(side="left", padx=4)
            tk.Button(right, text="Delete", bg="#d93025", fg="#fff", padx=10).pack(side="left", padx=4)
        return frame

    def _create_context_page(self) -> tk.Frame:
        frame = tk.Frame(self.content, bg="#f9f9f9")
        tk.Label(frame, text="Context Resources", font=("Arial", 20, "bold"), bg="#f9f9f9").pack(anchor="w", padx=20, pady=(20, 10))
        tk.Button(frame, text="+ Add new resource", bg="#1a73e8", fg="#fff", padx=12, pady=6, borderwidth=0).pack(anchor="w", padx=20, pady=(0, 20))
        resources_container = tk.Frame(frame, bg="#f9f9f9")
        resources_container.pack(fill="both", padx=20)
        resources_data = [
            {"name": "Calendar 2024", "desc": "Events and availability for the year 2024"},
            {"name": "Weather Forecast", "desc": "Get weather forecasts for any city and date"},
            {"name": "Trip History", "desc": "Past travel itineraries and preferences"},
        ]
        for res in resources_data:
            row = tk.Frame(resources_container, bg="#ffffff", bd=1, relief="solid")
            row.pack(fill="x", pady=4)
            left = tk.Frame(row, bg="#ffffff")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            tk.Label(left, text=res["name"], font=("Arial", 14, "bold"), bg="#ffffff").pack(anchor="w")
            tk.Label(left, text=res["desc"], font=("Arial", 10), fg="#666", bg="#ffffff").pack(anchor="w")
            right = tk.Frame(row, bg="#ffffff")
            right.pack(side="right", padx=10, pady=10)
            tk.Button(right, text="View", bg="#1a73e8", fg="#fff", padx=10).pack(side="left", padx=4)
        return frame

    def _create_prompts_page(self) -> tk.Frame:
        frame = tk.Frame(self.content, bg="#f9f9f9")
        tk.Label(frame, text="Prompt Templates", font=("Arial", 20, "bold"), bg="#f9f9f9").pack(anchor="w", padx=20, pady=(20, 10))
        tk.Button(frame, text="+ Add new prompt", bg="#1a73e8", fg="#fff", padx=12, pady=6, borderwidth=0).pack(anchor="w", padx=20, pady=(0, 20))
        prompts_container = tk.Frame(frame, bg="#f9f9f9")
        prompts_container.pack(fill="both", padx=20)
        prompts_data = [
            {"name": "Default Instruction", "desc": "General instructions for using the assistant"},
            {"name": "Travel Planning Prompt", "desc": "Template for planning travel itineraries"},
            {"name": "Email Draft Prompt", "desc": "Template for drafting professional emails"},
        ]
        for prm in prompts_data:
            row = tk.Frame(prompts_container, bg="#ffffff", bd=1, relief="solid")
            row.pack(fill="x", pady=4)
            left = tk.Frame(row, bg="#ffffff")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            tk.Label(left, text=prm["name"], font=("Arial", 14, "bold"), bg="#ffffff").pack(anchor="w")
            tk.Label(left, text=prm["desc"], font=("Arial", 10), fg="#666", bg="#ffffff").pack(anchor="w")
            right = tk.Frame(row, bg="#ffffff")
            right.pack(side="right", padx=10, pady=10)
            tk.Button(right, text="Edit", bg="#fbbc04", fg="#333", padx=10).pack(side="left", padx=4)
            tk.Button(right, text="Delete", bg="#d93025", fg="#fff", padx=10).pack(side="left", padx=4)
        return frame

    def _create_security_page(self) -> tk.Frame:
        frame = tk.Frame(self.content, bg="#f9f9f9")
        tk.Label(frame, text="Security & Permissions", font=("Arial", 20, "bold"), bg="#f9f9f9").pack(anchor="w", padx=20, pady=(20, 10))

        # Roles section
        roles_section = tk.Frame(frame, bg="#f9f9f9")
        roles_section.pack(fill="x", padx=20, pady=(0, 20))
        roles_header = tk.Frame(roles_section, bg="#f9f9f9")
        roles_header.pack(fill="x")
        tk.Label(roles_header, text="Roles", font=("Arial", 16, "bold"), bg="#f9f9f9").pack(side="left")
        tk.Button(roles_header, text="+ Add new role", bg="#1a73e8", fg="#fff", padx=10, pady=4, borderwidth=0).pack(side="right")
        roles_container = tk.Frame(roles_section, bg="#f9f9f9")
        roles_container.pack(fill="both", pady=(10, 0))
        roles_data = [
            {"name": "Administrator", "desc": "Full access to all servers, tools, and settings"},
            {"name": "Editor", "desc": "Can modify tools and context, but not server settings"},
            {"name": "Viewer", "desc": "Read‑only access to view servers, tools and logs"},
        ]
        for role in roles_data:
            row = tk.Frame(roles_container, bg="#ffffff", bd=1, relief="solid")
            row.pack(fill="x", pady=4)
            left = tk.Frame(row, bg="#ffffff")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            tk.Label(left, text=role["name"], font=("Arial", 14, "bold"), bg="#ffffff").pack(anchor="w")
            tk.Label(left, text=role["desc"], font=("Arial", 10), fg="#666", bg="#ffffff").pack(anchor="w")
            right = tk.Frame(row, bg="#ffffff")
            right.pack(side="right", padx=10, pady=10)
            tk.Button(right, text="Manage", bg="#fbbc04", fg="#333", padx=10).pack(side="left", padx=4)

        # Users section
        users_section = tk.Frame(frame, bg="#f9f9f9")
        users_section.pack(fill="x", padx=20)
        users_header = tk.Frame(users_section, bg="#f9f9f9")
        users_header.pack(fill="x")
        tk.Label(users_header, text="Users", font=("Arial", 16, "bold"), bg="#f9f9f9").pack(side="left")
        tk.Button(users_header, text="+ Add new user", bg="#1a73e8", fg="#fff", padx=10, pady=4, borderwidth=0).pack(side="right")
        users_container = tk.Frame(users_section, bg="#f9f9f9")
        users_container.pack(fill="both", pady=(10, 0))
        users_data = [
            {"name": "Alice", "role": "Administrator"},
            {"name": "Bob", "role": "Editor"},
            {"name": "Charlie", "role": "Viewer"},
        ]
        for user in users_data:
            row = tk.Frame(users_container, bg="#ffffff", bd=1, relief="solid")
            row.pack(fill="x", pady=4)
            left = tk.Frame(row, bg="#ffffff")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            tk.Label(left, text=user["name"], font=("Arial", 14, "bold"), bg="#ffffff").pack(anchor="w")
            tk.Label(left, text=user["role"], font=("Arial", 10), fg="#666", bg="#ffffff").pack(anchor="w")
            right = tk.Frame(row, bg="#ffffff")
            right.pack(side="right", padx=10, pady=10)
            tk.Button(right, text="Edit", bg="#fbbc04", fg="#333", padx=10).pack(side="left", padx=4)
            tk.Button(right, text="Delete", bg="#d93025", fg="#fff", padx=10).pack(side="left", padx=4)
        return frame

    def _create_logs_page(self) -> tk.Frame:
        frame = tk.Frame(self.content, bg="#f9f9f9")
        tk.Label(frame, text="System Logs", font=("Arial", 20, "bold"), bg="#f9f9f9").pack(anchor="w", padx=20, pady=(20, 10))
        # Filter controls
        controls = tk.Frame(frame, bg="#f9f9f9")
        controls.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(controls, text="Severity:", font=("Arial", 10, "bold"), bg="#f9f9f9").pack(side="left")
        severity_var = tk.StringVar(value="All")
        ttk.OptionMenu(controls, severity_var, "All", "All", "Info", "Warning", "Error").pack(side="left", padx=(4, 10))
        tk.Label(controls, text="Search:", font=("Arial", 10, "bold"), bg="#f9f9f9").pack(side="left")
        tk.Entry(controls, width=30).pack(side="left", padx=(4, 10))
        tk.Button(controls, text="Clear logs", bg="#d93025", fg="#fff", padx=10).pack(side="right")
        # Logs list
        logs_container = tk.Frame(frame, bg="#f9f9f9")
        logs_container.pack(fill="both", padx=20)
        logs_data = [
            {"date": "2025-10-01", "time": "14:23", "type": "INFO", "message": "Server 1 started successfully."},
            {"date": "2025-10-02", "time": "09:12", "type": "WARNING", "message": "Memory usage exceeded 80% threshold on Server 2."},
            {"date": "2025-10-03", "time": "21:45", "type": "ERROR", "message": "Failed to connect to database for Tool C."},
            {"date": "2025-10-04", "time": "08:30", "type": "INFO", "message": "New prompt 'Travel Planning Prompt' created."},
        ]
        for log in logs_data:
            color = {
                "INFO": "#34a853",
                "WARNING": "#fbbc04",
                "ERROR": "#d93025",
            }.get(log["type"], "#e0e0e0")
            entry = tk.Frame(logs_container, bg="#ffffff", bd=1, relief="solid")
            entry.pack(fill="x", pady=4)
            # colored indicator
            indicator = tk.Frame(entry, bg=color, width=5)
            indicator.pack(side="left", fill="y")
            meta_msg = tk.Frame(entry, bg="#ffffff")
            meta_msg.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            meta_text = f"{log['date']}  {log['time']}  {log['type']}"
            tk.Label(meta_msg, text=meta_text, font=("Arial", 9, "bold"), fg="#666", bg="#ffffff").pack(anchor="w")
            tk.Label(meta_msg, text=log["message"], font=("Arial", 10), fg="#333", bg="#ffffff").pack(anchor="w")
        return frame


if __name__ == "__main__":
    app = MCPAdminApp()
    app.mainloop()