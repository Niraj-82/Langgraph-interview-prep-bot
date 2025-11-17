
# LangGraph Interview Preparation Bot

## Overview
This project is a comprehensive mock interview preparation system built using **LangGraph**, a powerful framework for creating stateful, graph-based workflows. It simulates a realistic job interview experience for backend developer roles, particularly focusing on Python, REST APIs, databases, microservices, and DevOps practices.

The system operates as a state machine that guides users through the entire interview process, from initial job description parsing to final salary negotiation. Key features include:

- **Dynamic Question Generation**: Generates a mix of technical and behavioral questions tailored to the job description, with difficulty levels that adjust based on user performance.
- **Intelligent Evaluation**: Analyzes user responses using the STAR (Situation, Task, Action, Result) method, providing detailed feedback on structure, relevance, and depth.
- **Adaptive Difficulty**: Increases or decreases question complexity based on answer quality to maintain an appropriate challenge level.
- **Progress Tracking**: Monitors time usage, scores, and question types throughout the interview.
- **Comprehensive Reporting**: Produces a final report with average scores, strengths, areas for improvement, and next steps.
- **Salary Negotiation Phase**: Includes a dedicated phase for discussing compensation expectations.
- **Logging and Persistence**: Saves interview logs and transcripts for review and analysis.

The application uses LangChain's message handling for conversational flow and includes a question bank with predefined questions across various topics and difficulty levels.

## Features
✔ Question generation (technical + behavioral)  
✔ Follow-up logic & difficulty adjustment  
✔ Feedback with STAR method analysis  
✔ Confidence scoring + improvement tips  
✔ Progress tracking & final summary report  

## Requirements
- Python 3.8+
- langgraph
- langchain-core

## Installation
Install the required dependencies using pip:
```bash
pip install langgraph langchain-core
```

## How to Run
```bash
python graph.py
```

## Files
| File | Description |
|------|-------------|
| `graph.py` | Main LangGraph implementation |
| `question_bank.json` | Question bank for different types of questions |
| `README.md` | Project documentation |
| `interview_log.json` | Log file for interview sessions (generated during runtime) |
| `final_report.txt` | Final interview report (generated at the end of the interview) |
| `.gitignore` | Git ignore file |

## Example Output
```
Mock interview complete. Average score: 3.60/5.
Salary negotiation phase initiated.
```

## Future Scope
We can extend the interview system by:
- Adding more questions in `question_bank.json`
- Connecting to real LLMs for question and feedback generation
- Integrating company research / résumé parsing / video interviews
