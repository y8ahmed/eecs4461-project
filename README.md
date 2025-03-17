# The Domino Effect: TikTok Bot Echo Chambers
EECS4461 W25

## Team 12
- Yusuf AHMED
- Greatlove BARIBOLOKA
- Melika SHERAFAT

## A. Current Implementation State
Our prototype simulates TikTok bot interactions in a simplified environment. The current implementation includes:
- Basic bot interaction simulation
- Visualization of bot relationships and interactions
- Simple echo chamber formation tracking
- Interactive web interface for simulation control

## B. Running the Simulation

### Prerequisites
- Python 3.12
- Virtual environment (venv)

### Installation Steps
1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application
1. Navigate to the src directory:
   ```bash
   cd src
   ```
2. Start the application:
   ```bash
   solara run app.py
   ```
3. Open your browser and go to the displayed local URL (typically http://localhost:8765)

## C. Limitations and Future Improvements
Current limitations:
- Simplified bot behavior models
- Basic interaction mechanics
- Limited data visualization options

Planned improvements:
- Enhanced bot behavior complexity
- More sophisticated interaction patterns
- Advanced visualization features
- Improved data collection and analysis tools

## Navigate to the relevant directory for each deliverable:
- docs/Deliverable1 - General Project Idea and Team Expectations
- docs/Deliverable2 - Project Proposal 
- docs/Deliverable3 - Simple Simulation Prototype

## Project Description
The TikTok Echo Chamber Model simulates the formation and sustenance of echo chambers by bot to bot interactions on TikTok. 

## Run the Project
Clone the repo

In root eecs4461-project directory, **create a venv** - commands vary per OS so review the linked guides
- Install [python3.12](https://www.python.org/downloads/release/python-3128/)
- Install [venv](https://realpython.com/python-virtual-environments-a-primer/)

Go into the src directory
`cd src`

- Create venv `python -m venv venv`
- Activate venv `source venv/bin/activate`

Install packages based on requirements.txt
`pip install -r requirements.txt`

Run solara
`solara run app.py`
