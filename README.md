Minecraft Material Manager

Active Tracking and Resource Calculator for Litematica Schematics

Minecraft Material Manager is a desktop application tailored specifically for the technical Minecraft community, mega-build creators, and anyone using the Litematica mod to plan their in-game structures.

When managing large-scale projects, resource tracking becomes notoriously complex. While Litematica provides a complete block list, it lacks a dynamic tool to track collected items against missing ones or to calculate totals using native in-game units (Shulker Boxes and Stacks). This application bridges that gap, automating resource calculations and interfacing directly with Litematica data.
Key Features

    Minecraft-Shorthand Math Compiler
    Input and aggregate block quantities using in-game terminology. Expressions like 1sb + 12stk + 32 instantly evaluate to a total of 2,528 single blocks. The parser natively supports modifiers such as sb (Shulker Box: 1,728 blocks), stk / stack (64 blocks), and complex mathematical formulas.

    Native Litematica Integration
    Equipped with dedicated regex scanning filters to recognize Litematica's table layouts. It cleans formatted text by stripping graphical borders, instantly isolating block names and their required quantities.

    Raw Material Breakdown
    Features an internal crafting engine capable of analyzing both shaped and shapeless recipes. If a project requires a crafted item, the application can decompose it down to its fundamental raw materials.

    Advanced & Differential Tracking
    Input your currently collected materials to calculate exactly what is left to gather in real time. Visual progress bars integrated into the GUI provide an instant overview of your project's status.

    Optimized Graphical Interface
    A modern user interface powered by the Sun Valley dark theme, featuring desktop optimizations for Windows environments via pywinstyles to ensure a clean, comfortable view during long gaming sessions.

    Automated Package Management
    Zero manual terminal configuration required. The script automatically checks for required Python modules (Pillow, tkinterdnd2, pywinstyles, sv-ttk, litemapy) and handles background installation during the initial launch.

Litematica Usage Guide

The application is engineered to eliminate manual transcription. Follow these steps to extract material lists from your builds and import them into the program.
1. Extracting the Material List from Litematica

    Open the Litematica configuration menu inside Minecraft (default key: M).

    Navigate to Schematic Placements (or use the Task Manager if tracking an active build).

    Find your schematic and click the Material List button.

    From the item layout screen, choose one of two options:

        Click Copy to Clipboard at the bottom to copy the formatted table data.

        Click Dump to File to save the list as a .txt file inside your Minecraft configurations directory.

2. Importing and Processing Data

    Clipboard Import: Select your active project inside Minecraft Material Manager and use the quick import feature. The application will scan the text, bypass mod headers (such as Item, Total, Missing columns), and save only valid block entries to the database.

    File Import (Drag and Drop): Drag your Litematica .txt dump file directly into the application window. The core/scanner.py engine will apply regex patterns to extract all block data in less than a second.

Evaluation Engine Examples

The evaluation parser translates short-form expressions securely and formats them cleanly back into the user interface:
Input String	Translated Expression	Total Blocks	Formatted Output
1sb	1 * 1728	1728	1SB
2stk + 10	2 * 64 + 10	138	2stk + 10
1sb + 5stk	1 * 1728 + 5 * 64	2048	1SB + 5^
Code Architecture

The codebase is split into modular components to streamline development and future expansions:

├── core/
│   ├── config.py       # General configurations (JSON) and dark palette definitions
│   ├── database.py     # Project database, tracking states, and recipe breakdown
│   ├── scanner.py      # Text-parsing engine for TXT, JSON, and Litematica tables
│   └── utils.py        # Math utilities, shorthand processing, and regex filters
└── ui/
    ├── components.py   # Reusable UI elements, custom dialogues, Canvas progress bars
    └── main_window.py  # Main application window setup and GUI logic flows

Installation & Setup
Prerequisites

    Python 3.8 or higher must be installed on your system.

Configuration Steps

Clone the repository and launch the main application script:
Bash

git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
python main.py

License

This project is licensed under the MIT License - see the LICENSE file for details.
