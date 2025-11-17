
# LangGraph Interview Preparation Bot

## Overview
This project is a mock interview system built using **LangGraph** that:
- Generates interview questions based on a job description
- Adjusts difficulty dynamically
- Evaluates candidate answers
- Provides STAR-based structured feedback
- Produces a final interview report

## Features
✔ Question generation (technical + behavioral)  
✔ Follow-up logic & difficulty adjustment  
✔ Feedback with STAR method analysis  
✔ Confidence scoring + improvement tips  
✔ Progress tracking & final summary report  
✔ Salary negotiation phase  

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

## Extend
You can extend the interview system by:
- Adding more questions in `question_bank.json`
- Connecting to real LLMs for question and feedback generation
- Integrating company research / résumé parsing / video interviews
