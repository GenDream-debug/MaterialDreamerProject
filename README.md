Minecraft Material Manager

Graphic User Interface for Litematica Material Lists and Shorthand Calculations.

Minecraft Material Manager is a dedicated desktop application engineered specifically for the Technical Minecraft community, mega-build creators, and players utilizing the Litematica mod to plan complex in-game structures.

While Litematica excels at generating comprehensive block lists, managing those resources over large-scale projects can quickly become overwhelming. It lacks a dynamic interface to track currently gathered materials against remaining needs, nor does it naturally convert raw item counts into standard in-game metrics like Shulker Boxes and Stacks. This application fills that gap by automating resource math and integrating seamlessly with your Litematica data.
🚀 Key Features

    📐 Minecraft-Shorthand Math Engine: Input and calculate material quantities instantly using intuitive game-specific shorthand. Typing strings like 1sb + 12stk + 32 instantly translates to exactly 2,528 individual blocks. The custom parser supports modifiers such as sb (Shulker Box / 1,728 blocks), stk or stack (64 blocks), and complex mathematical operators.

    🔌 Native Litematica Parsing: Features custom Regex filtering engines designed to interpret and clean raw Litematica table dumps. It strips away formatting lines, borders, and UI artifacts, isolating item IDs and required quantities in milliseconds.

    🌳 Crafting Tree Deconstruction: Includes an integrated crafting recipe database (supporting shaped and shapeless designs). If a schematic calls for composite items (e.g., Hoppers or Pistons), the app can break them down into their exact, base raw material requirements (Iron, Wood, Redstone).

    📊 Real-Time Delta Tracking: Log your gathered resources on the fly. The engine updates instantly to display a precise delta (remaining materials required) paired with dynamic progress bars built directly into the UI.

    🎨 Modern UX/UI Design: Built on a customized, dark-themed Sun Valley aesthetic with deep Win32 optimizations powered by pywinstyles. This guarantees a sleek, distraction-free environment tailored for long gaming sessions.

    🛠️ Zero-Config Dependency Management: Skip the terminal setup. Upon initial boot, the core script automatically runs an internal package audit. If required dependencies (Pillow, tkinterdnd2, pywinstyles, sv-ttk, litemapy) are missing, it safely installs them in the background.

📖 Litematica Integration Guide

Say goodbye to manual data entry. Here is how to seamlessly bridge your schematics directly into the manager.
1. Exporting the Material List from Litematica

    Inside your Minecraft world, open the Litematica configuration menu (Default key bind: M).

    Navigate to Schematic Placements (or use the Task Manager if working with an active build).

    Find your desired schematic configuration and click Material List.

    At the bottom of the block overview screen, select one of two export methods:

        Copy to Clipboard: Copies the formatted table directly to your system clipboard.

        Dump to File: Generates a .txt file containing the clean dataset within your Minecraft configurations folder.

2. Importing into the Application

    Clipboard Swift-Import: In Minecraft Material Manager, open your active project and click the clipboard import utility. The module filters out mod-specific headers (such as Item, Total, Missing columns) and populates your project database strictly with valid blocks.

    Drag and Drop Files: Select the .txt document created by Litematica's "Dump to File" command and drop it anywhere into the application window. The core/scanner.py engine will process the regex and update your workspace instantly.

🧮 Evaluation Engine Examples

The evaluation engine securely handles shorthand math expressions and applies clean reverse-formatting within the user interface:
Input String	Parsed Expression	Total Blocks	Display Format
1sb	1 × 1728	1728	1 SB
2stk + 10	(2 × 64) + 10	138	2 stk + 10
1sb + 5stk	(1 × 1728) + (5 × 64)	2048	1 SB + 5 stk
🗂️ Project Architecture

The software follows a highly modular layout designed for quick expansion and code readability:
YAML

├── core/
│   ├── config.py       # Global JSON preferences and dark-mode palette values
│   ├── database.py     # Workspace management, delta tracking, and item recipe trees
│   ├── scanner.py      # Main text parsing engine for Litematica TXT and JSON exports
│   └── utils.py        # Shorthand math translation rules and core Regex filters
└── ui/
    ├── components.py   # Reusable UI widgets, dialogues, and Canvas progress bars
    └── main_window.py  # Primary window controller and layout logic orchestration

💻 Installation & Quickstart
Prerequisites

    Python 3.8 or higher must be installed on your operating system.

Getting Started

Clone the repository or download the source code package to your local machine:
Bash

# Clone the repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Navigate to the project directory
cd YOUR_REPO_NAME

# Launch the application (missing packages will install automatically)
python main.py
