#!/usr/bin/env python3
"""
Display Utilities
Terminal colors, formatting, and UI components
"""
import os

# Terminal colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
BOLD = '\033[1m'
RESET = '\033[0m'

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header(title, width=75, color=BLUE):
    """Print formatted header"""
    print(f"\n{BOLD}{color}{'='*width}{RESET}")
    print(f"{BOLD}{color}{title:^{width}}{RESET}")
    print(f"{BOLD}{color}{'='*width}{RESET}\n")

def print_section(title):
    """Print section title"""
    print(f"\n{BOLD}{title}{RESET}")

def format_price(price):
    """Format price with appropriate decimals"""
    if price < 0.01:
        return f"${price:.6f}"
    elif price < 1:
        return f"${price:.4f}"
    elif price < 100:
        return f"${price:.2f}"
    else:
        return f"${price:,.2f}"

def format_percent(value, colored=True):
    """Format percentage with color"""
    if colored:
        color = GREEN if value >= 0 else RED
        return f"{color}{value:+.2f}%{RESET}"
    return f"{value:+.2f}%"

def format_volume(volume):
    """Format volume with K/M/B suffix"""
    if volume >= 1_000_000_000:
        return f"${volume/1_000_000_000:.2f}B"
    elif volume >= 1_000_000:
        return f"${volume/1_000_000:.2f}M"
    elif volume >= 1_000:
        return f"${volume/1_000:.2f}K"
    else:
        return f"${volume:.2f}"
