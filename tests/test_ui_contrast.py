import unittest
import sys
import os
import logging
import re
import cssutils
from bs4 import BeautifulSoup

# Suppress cssutils warnings
cssutils.log.setLevel(logging.CRITICAL)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestUIContrast(unittest.TestCase):
    """Tests for ensuring UI elements have proper contrast"""
    
    def setUp(self):
        """Set up test environment"""
        self.css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                     'static', 'css', 'custom.css')
        
        # Load the CSS file
        with open(self.css_path, 'r') as f:
            self.css_content = f.read()
            
        # Parse CSS
        self.css = cssutils.parseString(self.css_content)
    
    def test_button_text_color(self):
        """Test that all button text colors are set to white for maximum contrast"""
        # Find all button-related selectors
        button_selectors = []
        
        for rule in self.css.cssRules:
            if hasattr(rule, 'selectorText'):
                selector = rule.selectorText.lower()
                if any(term in selector for term in ['.btn', 'button', 'a[href', '.action-button', '.glow-button']):
                    button_selectors.append(rule)
        
        # We should have found at least some button selectors
        self.assertGreater(len(button_selectors), 0, "Should find button-related CSS rules")
        
        # Check for white text color rules
        white_text_rules = []
        for rule in self.css.cssRules:
            if hasattr(rule, 'selectorText') and hasattr(rule, 'style'):
                if 'color' in rule.style.keys():
                    color_value = rule.style.getPropertyValue('color').lower()
                    if '#ffffff' in color_value or 'white' in color_value:
                        # Check if this rule applies to buttons
                        selector = rule.selectorText.lower()
                        if any(term in selector for term in ['.btn', 'button', 'a[href', '.action-button', '.glow-button']):
                            white_text_rules.append(rule)
        
        # We should have found white text rules for buttons
        self.assertGreater(len(white_text_rules), 0, 
                          "Should find CSS rules that set button text to white")
        
        # Make sure "!important" is used to force white text
        important_rules = []
        for rule in white_text_rules:
            if hasattr(rule, 'style'):
                if 'color' in rule.style.keys():
                    color_value = rule.style.getPropertyValue('color')
                    # Check if !important is in the rule
                    if '!important' in rule.style.getCssText():
                        important_rules.append(rule)
        
        # We should have found !important rules for white text
        self.assertGreater(len(important_rules), 0, 
                          "Should find CSS rules that set button text to white with !important")
        
        # Verify specific button types have white text rules
        button_types = [
            ('login button', ['.login-btn', 'a[href*="login"]', '.btn-login']),
            ('register button', ['.register-btn', 'a[href*="register"]', '.btn-register']),
            ('optimize button', ['a[href*="optimize"]', '.action-button']),
            ('primary button', ['.btn-primary', '.glow-button']),
            ('secondary button', ['.btn-secondary', '.action-button'])
        ]
        
        for button_name, selectors in button_types:
            found = False
            for rule in self.css.cssRules:
                if hasattr(rule, 'selectorText'):
                    rule_selectors = rule.selectorText.split(',')
                    for rule_selector in rule_selectors:
                        rule_selector = rule_selector.strip().lower()
                        if any(selector.lower() in rule_selector for selector in selectors):
                            if hasattr(rule, 'style') and 'color' in rule.style.keys():
                                color_value = rule.style.getPropertyValue('color').lower()
                                if '#ffffff' in color_value or 'white' in color_value:
                                    found = True
            
            self.assertTrue(found, f"Should find white text rule for {button_name}")
    
    def test_button_hover_color(self):
        """Test that all button hover states maintain white text color"""
        # Find all button hover selectors
        hover_selectors = []
        
        for rule in self.css.cssRules:
            if hasattr(rule, 'selectorText'):
                selector = rule.selectorText.lower()
                if ':hover' in selector and any(term in selector for term in ['.btn', 'button', 'a[href', '.action-button', '.glow-button']):
                    hover_selectors.append(rule)
        
        # We should have found at least some button hover selectors
        self.assertGreater(len(hover_selectors), 0, "Should find button hover CSS rules")
        
        # Check for white text color in hover rules
        white_hover_rules = []
        for rule in hover_selectors:
            if hasattr(rule, 'style'):
                if 'color' in rule.style.keys():
                    color_value = rule.style.getPropertyValue('color').lower()
                    if '#ffffff' in color_value or 'white' in color_value:
                        white_hover_rules.append(rule)
        
        # We should have found white text rules for button hovers
        self.assertGreater(len(white_hover_rules), 0, 
                          "Should find CSS rules that set button hover text to white")
    
    def test_dark_input_background(self):
        """Test that form inputs have dark backgrounds for good contrast with white text"""
        # Find input/form field selectors
        input_selectors = []
        
        for rule in self.css.cssRules:
            if hasattr(rule, 'selectorText'):
                selector = rule.selectorText.lower()
                if any(term in selector for term in ['.form-control', '.form-select', 'input']):
                    input_selectors.append(rule)
        
        # We should have found at least some input selectors
        self.assertGreater(len(input_selectors), 0, "Should find input field CSS rules")
        
        # Check for dark background colors
        dark_bg_rules = []
        for rule in input_selectors:
            if hasattr(rule, 'style'):
                if 'background-color' in rule.style.keys():
                    bg_value = rule.style.getPropertyValue('background-color').lower()
                    # Look for rgba with low values (dark colors)
                    if 'rgba(' in bg_value:
                        rgba_match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+)', bg_value)
                        if rgba_match:
                            r, g, b = map(int, rgba_match.groups())
                            # Check if it's a dark color (average RGB < 100)
                            if (r + g + b) / 3 < 100:
                                dark_bg_rules.append(rule)
        
        # We should have found dark background rules for inputs
        self.assertGreater(len(dark_bg_rules), 0, 
                          "Should find CSS rules that set input backgrounds to dark colors")

if __name__ == '__main__':
    unittest.main()