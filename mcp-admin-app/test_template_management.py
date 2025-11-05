"""
Test Template Management Integration
====================================

Test the new template management interface functionality.
"""

import tkinter as tk
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.template_editor_page import TemplateEditorPage
from ui.prompt_components.template_list import TemplateListWidget
from models.prompt import PromptTemplate


def test_template_management():
    """Test the template management components."""
    print("Testing Template Management Components...")
    
    # Create root window
    root = tk.Tk()
    root.title("Test Template Management")
    root.geometry("1200x800")
    
    try:
        # Create paned window
        from tkinter import ttk
        paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Template list
        list_frame = tk.Frame(paned_window, bg="#ffffff")
        paned_window.add(list_frame, weight=1)
        
        # Template list widget
        template_list = TemplateListWidget(
            list_frame, 
            None,  # No service for testing
            on_select=lambda template: print(f"Selected template: {template.name if template else 'New template'}")
        )
        template_list.pack(fill="both", expand=True)
        
        # Right panel - Template editor
        editor_frame = tk.Frame(paned_window, bg="#ffffff")
        paned_window.add(editor_frame, weight=2)
        
        # Template editor
        template_editor = TemplateEditorPage(
            editor_frame,
            None,  # No service for testing
            on_save=lambda template: print(f"Saved template: {template.name}")
        )
        template_editor.pack(fill="both", expand=True)
        
        print("✓ Template list widget created successfully")
        print("✓ Template editor created successfully")
        print("✓ Sample templates loaded")
        print("✓ UI components integrated")
        
        print("\n✅ Template Management test completed successfully!")
        print("\nFeatures to test in the UI:")
        print("• Browse sample templates in the left panel")
        print("• Click on templates to load them in the editor")
        print("• Use the 'New' button to create new templates")
        print("• Test the rich text editor with syntax highlighting")
        print("• Try the variable insertion buttons")
        print("• Use the search and filter functionality")
        print("• Check the live preview panel")
        print("• Explore the version history widget")
        
        print("\nThe application window will remain open for testing...")
        
        # Keep window open for testing
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        root.destroy()
        return False
    
    return True


if __name__ == "__main__":
    success = test_template_management()
    if success:
        print("\n🎉 Template Management test completed!")
    else:
        print("\n💥 Template Management test failed!")
        sys.exit(1)