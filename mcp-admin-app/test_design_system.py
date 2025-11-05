#!/usr/bin/env python3
"""
Test script for the refactored design system.
"""

import tkinter as tk
from ui.design_system import DesignSystem, ColorPalette, Typography, Spacing

def test_design_system():
    """Test the design system components."""
    root = tk.Tk()
    root.title("Design System Test")
    root.geometry("600x400")
    
    # Test color access
    print("Testing color access:")
    print(f"Background color: {DesignSystem.colors['background']}")
    print(f"Primary accent: {DesignSystem.colors['accent_primary']}")
    
    # Test typography
    print("\nTesting typography:")
    font_config = DesignSystem.get_font('headline_large')
    print(f"Headline font: {font_config}")
    
    # Test component creation
    print("\nTesting component creation:")
    
    # Create a test frame
    test_frame = tk.Frame(root, bg=DesignSystem.colors['background'])
    test_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    # Test section header
    header = DesignSystem.create_section_header(
        test_frame, 
        "Test Header", 
        "This is a test subtitle"
    )
    header.pack(fill='x', pady=(0, 20))
    
    # Test buttons
    button_frame = tk.Frame(test_frame, bg=DesignSystem.colors['background'])
    button_frame.pack(fill='x', pady=(0, 20))
    
    primary_btn = DesignSystem.create_button(button_frame, "Primary Button", "primary")
    primary_btn.pack(side='left', padx=(0, 10))
    
    secondary_btn = DesignSystem.create_button(button_frame, "Secondary Button", "secondary")
    secondary_btn.pack(side='left', padx=(0, 10))
    
    ghost_btn = DesignSystem.create_button(button_frame, "Ghost Button", "ghost")
    ghost_btn.pack(side='left')
    
    # Test input field
    input_field = DesignSystem.create_input(test_frame)
    input_field.pack(fill='x', pady=(0, 20))
    input_field.insert(0, "Test input field")
    
    # Test stats card
    stats_frame = tk.Frame(test_frame, bg=DesignSystem.colors['background'])
    stats_frame.pack(fill='x', pady=(0, 20))
    
    stats_card = DesignSystem.create_stats_card(stats_frame, "42", "Test Metric")
    stats_card.pack(side='left', padx=(0, 20))
    
    # Test divider
    divider = DesignSystem.create_divider(test_frame)
    divider.pack(fill='x', pady=10)
    
    # Test label
    label = DesignSystem.create_label(test_frame, "Test label with body_medium style")
    label.pack(anchor='w')
    
    print("All components created successfully!")
    
    # Don't start mainloop in test
    root.update()
    root.destroy()
    
    return True

if __name__ == "__main__":
    try:
        success = test_design_system()
        if success:
            print("\n✅ Design system test passed!")
        else:
            print("\n❌ Design system test failed!")
    except Exception as e:
        print(f"\n❌ Design system test failed with error: {e}")
        import traceback
        traceback.print_exc()