# The Domino Effect: TikTok Bot Echo Chambers
EECS4461 W25

## Team 12
- Yusuf AHMED
- Greatlove BARIBOLOKA
- Melika SHERAFAT

## Project Description
The TikTok Echo Chamber Model simulates the formation and sustenance of echo chambers by bot to bot interactions on TikTok.

## A. Overview of the Phenomenon
Echo chambers in social media represent a critical challenge in modern information ecosystems, particularly in how AI-driven bots interact with both human users and other automated agents. Our ABM model specifically investigates this dynamic on TikTok, where automated agents can create self-sustaining information bubbles that significantly impact public discourse. As demonstrated in "The Spreading of Misinformation Online," these echo chambers can facilitate the rapid propagation of false or misleading information, often outpacing verified content due to emotional engagement and algorithmic promotion (Del Vicario et al., 2016).
The significance of AI-to-AI interactions in this context is particularly concerning. When bots interact with other bots, they can create a feedback loop that amplifies specific narratives and viewpoints. This higher interaction rate among bots can create an artificial sense of consensus or popularity around certain viewpoints, as demonstrated in the study of 'Urbanist Uma' and similar social media bots (Johnson et al., 2023). Our model captures this through weighted interactions (FOLLOW=5, SHARE=3, LIKE=2, COMMENT=2, VIEW=1) that demonstrate how different types of engagement contribute to echo chamber formation.

Our prototype simulates TikTok bot interactions in a sophisticated environment. The current implementation includes:
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

## C. Key Findings
The cluster formation analysis shows that small clusters merge over time, resulting in a few large, ideologically similar groups. The final structure consists of three primary clusters, with a progressive-majority group (18 agents) and a smaller conservative group (2 agents). The cross-cluster interaction rate starts relatively high but declines as ideological clusters solidify. By the final stage, most interactions occur within ideological groups, simulating real-world echo chamber effects.
The line graph of ideological shifts indicates a steep decline in neutral agents, with a corresponding rise in progressive agents. The Conservative/Progressive Ratio (0.11) suggests that progressive ideology dominates the discourse, aligning with past studies on algorithmic amplification. Interestingly, progressive agents tend to engage more actively, using follows, shares, and likes, while conservatives exhibit lower engagement rates. This self-reinforcing cycle makes progressive content more visible, leading more agents to adopt it.

Improvements:
- Enhanced bot behavior complexity
- More sophisticated interaction patterns
- Advanced visualization features
- Improved data collection and analysis tools

## Navigate to the relevant directory for each deliverable:
- docs/Deliverable1 - General Project Idea and Team Expectations
- docs/Deliverable2 - Project Proposal 
- docs/Deliverable3 - Simple Simulation Prototype
- docs/Deliverable4 - Final Prototype and Analysis

