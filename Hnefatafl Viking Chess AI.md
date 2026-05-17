Hnefatafl: Viking Chess AI
A streamlined implementation of the ancient Norse strategy game Hnefatafl (9x9 Copenhagen variant). This project utilizes a specialized Prolog logic engine for game rules and AI, integrated with a Python graphical interface.

 Game Overview
Hnefatafl is an asymmetrical strategy game. A small force of Defenders must protect their King and escort him to a corner square. Meanwhile, a larger army of 24 Attackers attempts to surround and capture him.

 Key Features
Alpha-Beta AI: A competitive AI opponent using minimax search with alpha-beta pruning.

Dual-Role Gameplay: Play as either the Attacker or the Defender against the computer or a local friend.

Difficulty Tiers: Selectable AI depths (Easy, Medium, Hard) to challenge different skill levels.

Traditional Ruleset: Includes custodial captures, restricted squares (Throne/Corners), and specific king-capture logic.

 Technical Architecture
The project is split into two primary components:

hnefatafl.pl (The Brain): A comprehensive Prolog file containing the entire game engine, including board representation, movement rules, capture logic, and the alpha-beta search algorithm with custom heuristics.

GUI_hnefatafl.py (The Body): A Python script using the Pygame library to handle the visual interface, user interactions, and the communication bridge to the Prolog engine.

 AI Heuristics
The AI evaluates the board using a weighted utility function within hnefatafl.pl:

Material Weighting: Defenders are valued higher than attackers to account for their limited numbers.

Tactical Pressure: The AI actively monitors how many attackers are adjacent to the King.

Escape Route Analysis: The engine detects clear paths to corners and penalizes the AI if the King is allowed to reach an edge.

Manhattan Distance: Tracks the King’s proximity to victory corners to influence defensive and offensive positioning.

Project Files
GUI_hnefatafl.py: The main entry point. Run this file to start the game.

hnefatafl.pl: The complete logic and AI engine.

Requirements & Installation
Python 3.x

Pygame Library:

Bash
pip install pygame
SWI-Prolog: Must be installed and added to your system's PATH (environment variables).

 How to Run
Ensure both files are in the same directory and execute the GUI script:

Bash
python GUI_hnefatafl.py