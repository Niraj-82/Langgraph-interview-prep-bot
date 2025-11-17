
from typing import TypedDict, List, Dict, Any, Optional, Literal
from typing_extensions import Annotated

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

class QuestionRecord(TypedDict):
    id: str
    text: str
    type: Literal["technical", "behavioral", "mixed"]
    difficulty: Literal["easy", "medium", "hard"]
    topic: str

class AnswerRecord(TypedDict):
    question_id: str
    user_answer: str
    score: float
    confidence: Literal["low", "medium", "high"]
    star_usage: Dict[str, bool]
    feedback: str
    time_taken_sec: float

class InterviewState(TypedDict, total=False):
    job_description: str
    user_role: str
    target_company: Optional[str]
    jd_summary: str
    required_skills: List[str]
    soft_skills: List[str]
    seniority: str
    company_insights: str
    role_analysis: str
    competencies: List[str]
    max_questions: int
    asked_questions: List[QuestionRecord]
    answers: List[AnswerRecord]
    difficulty: Literal["easy", "medium", "hard"]
    question_counter: int
    current_question: Optional[QuestionRecord]
    start_time: Optional[float]
    awaiting_answer: bool
    time_budget_min: int
    estimated_time_used_min: float
    final_report: Optional[str]
    messages: List[Any]
    should_follow_up: bool = False
    salary_negotiation_phase: bool = False
    interview_complete: bool = False
    prepare_next_question: bool = False
    behavioral_questions: int = 0
    technical_questions: int = 0

import json, os, time

try:
    with open(os.path.join(os.path.dirname(__file__), "question_bank.json")) as f:
        QUESTION_BANK = json.load(f)
except:
    QUESTION_BANK = []

def parse_job_description(state: InterviewState) -> dict:
    jd = state.get("job_description", "")
    role = state.get("user_role", "Candidate")

    summary = (
        f"The role of {role} requires a candidate with proven experience in backend development, "
        "specifically with Python and RESTful APIs. The candidate will be responsible for designing, "
        "building, and maintaining scalable microservices. Key responsibilities include database management (SQL), "
        "writing unit and integration tests, and deploying applications using Docker. The ideal candidate "
        "is a collaborative individual who can solve complex problems and communicate effectively."
    )
    required_skills = ["Python", "REST APIs", "Microservices", "SQL", "Docker", "Unit Testing", "CI/CD"]
    soft_skills = ["Communication", "Teamwork", "Problem Solving", "Ownership"]

    if "senior" in jd.lower() or "lead" in jd.lower():
        seniority = "Senior"
    elif "junior" in jd.lower() or "entry" in jd.lower():
        seniority = "Junior"
    else:
        seniority = "Mid-level"

    return {
        "jd_summary": summary,
        "required_skills": required_skills,
        "soft_skills": soft_skills,
        "seniority": seniority,
    }

def research_company(state: InterviewState) -> dict:
    company = state.get("target_company")
    if not company:
        insights = (
            "The company is a fast-growing tech firm in the SaaS sector. They are known for a flat "
            "organizational structure, encouraging innovation from all levels. Their tech stack is modern, "
            "often centered around cloud-native technologies and agile practices. They value engineers who "
            "are product-minded and can take initiative."
        )
        return {"company_insights": insights}

    insights = (
        f"{company} is a leader in the FinTech space, known for its cutting-edge payment processing solutions. "
        "Their engineering culture emphasizes reliability, security, and scalability. They operate in a highly "
        "regulated environment, so attention to detail and robust testing are critical. Technologically, "
        f"they leverage a microservices architecture on AWS, with a strong focus on serverless technologies. "
        "The company values collaboration and has a reputation for a healthy work-life balance."
    )
    return {"company_insights": insights}

def analyze_role(state: InterviewState) -> dict:
    role_analysis = (
        "This is a mid-level backend role where the primary focus is on building and scaling microservices. "
        "The candidate must have strong fundamentals in API design and database management. Given the company's "
        "FinTech focus, there is a high emphasis on code quality, security, and robust testing. The role requires "
        "not just technical execution but also collaboration with product and DevOps teams. The ideal candidate "
        "will be a proactive problem-solver who can take ownership of features from conception to deployment."
    )

    competencies = [
        "Technical: Python & REST APIs",
        "Technical: Database Management (SQL)",
        "Technical: Microservices Architecture",
        "Technical: Testing & Debugging",
        "Technical: Cloud & DevOps (Docker, CI/CD)",
        "Behavioral: Problem Solving",
        "Behavioral: Team Collaboration",
        "Behavioral: Ownership & Accountability",
        "Behavioral: Communication Skills"
    ]

    return {
        "role_analysis": role_analysis,
        "competencies": competencies,
        "difficulty": state.get("difficulty", "medium"),
        "question_counter": 0,
        "asked_questions": [],
        "answers": [],
        "awaiting_answer": False,
        "time_budget_min": state.get("time_budget_min", 15),
        "estimated_time_used_min": 0.0,
        "behavioral_questions": 0,
        "technical_questions": 0,
    }

def _select_question(state: InterviewState) -> Optional[QuestionRecord]:
    used_ids = {q["id"] for q in state.get("asked_questions", [])}
    difficulty = state.get("difficulty", "medium")
    candidates = [q for q in QUESTION_BANK if q["difficulty"] in [difficulty, "medium"] and q["id"] not in used_ids]
    if not candidates:
        candidates = [q for q in QUESTION_BANK if q["id"] not in used_ids]
    if not candidates:
        return None
    return candidates[0]

def generate_question(state: InterviewState) -> dict:
    max_q = state.get("max_questions", 5)
    if state.get("question_counter", 0) >= max_q:
        return {"current_question": None}

    q = _select_question(state)
    if q is None:
        return {"current_question": None}

    new_asked_questions = state["asked_questions"] + [q]
    new_messages = state.get("messages", []) + [AIMessage(content=f"Question: {q['text']}")]

    update = {
        "current_question": q,
        "start_time": time.time(),
        "question_counter": state["question_counter"] + 1,
        "asked_questions": new_asked_questions,
        "awaiting_answer": True,
        "messages": new_messages,
    }

    if q["type"] == "behavioral":
        update["behavioral_questions"] = state.get("behavioral_questions", 0) + 1
    elif q["type"] == "technical":
        update["technical_questions"] = state.get("technical_questions", 0) + 1

    return update


def generate_follow_up_question(state: InterviewState) -> dict:
    if not state.get("should_follow_up"):
        return {}

    previous_question = state["current_question"]
    msgs = state["messages"]
    previous_answer = next((m.content for m in reversed(msgs) if isinstance(m, HumanMessage)), "")

    follow_up_text = f"That's an interesting point about '{previous_answer[:20]}...'. Can you elaborate on the challenges you faced?"

    follow_up_question: QuestionRecord = {
        "id": f"followup_{previous_question['id']}",
        "text": follow_up_text,
        "type": previous_question["type"],
        "difficulty": previous_question["difficulty"],
        "topic": previous_question["topic"],
    }

    new_asked_questions = state["asked_questions"] + [follow_up_question]
    new_messages = state["messages"] + [AIMessage(content=f"Follow-up: {follow_up_question['text']}")]

    return {
        "current_question": follow_up_question,
        "start_time": time.time(),
        "question_counter": state["question_counter"] + 1,
        "asked_questions": new_asked_questions,
        "awaiting_answer": True,
        "messages": new_messages,
        "should_follow_up": False, # Reset the flag
    }



def evaluate_answer(state: InterviewState) -> dict:
    if not state.get("awaiting_answer"):
        return {}
    q = state["current_question"]
    if not q:
        return {}

    msgs = state["messages"]
    ans = next((m.content for m in reversed(msgs) if isinstance(m, HumanMessage)), "")
    lower = ans.lower()

    star = {
        "S": any(w in lower for w in ["situation", "context", "background", "scenario", "role", "previous", "company", "corp"]),
        "T": any(w in lower for w in ["task", "goal", "responsibility", "assigned", "tasked", "objective", "challenge"]),
        "A": any(w in lower for w in ["action", "implemented", "did", "used", "applied", "developed", "created", "built", "handled"]),
        "R": any(w in lower for w in ["result", "impact", "outcome", "achieved", "improved", "reduced", "increased", "handled", "traffic"])
    }
    star_score = sum(star.values()) / 4  # 0-1
    rel = 1.0 if any(skill.lower() in lower for skill in state.get("required_skills", [])) else 0.5  # 0.5-1
    detail = min(len(ans.split()) / 80, 1.0)  # 0-1
    score = round((star_score * 0.5 + rel * 0.3 + detail * 0.2) * 5, 2)  # Weighted scoring

    if score >= 4.0:
        conf = "high"
    elif score >= 2.8:
        conf = "medium"
    else:
        conf = "low"

    # Calculate individual scores for feedback
    star_score_percent = star_score * 100
    relevance_score_percent = rel * 100
    depth_score_percent = detail * 100

    # Construct feedback in specified format
    star_coverage = "S=" + ("Present" if star["S"] else "Missing") + ", T=" + ("Present" if star["T"] else "Missing") + ", A=" + ("Present" if star["A"] else "Missing") + ", R=" + ("Present" if star["R"] else "Missing")

    improvement_suggestions = []
    if star_score < 1.0:
        missing = [k for k, v in star.items() if not v]
        improvement_suggestions.append(f"You explained the situation, task, and action well." if sum(star.values()) >= 3 else f"Structure your answer using STAR: Missing {', '.join(missing)}.")
        improvement_suggestions.append("Include measurable impact for the Result, e.g. reduced outage time, improved response time, etc." if not star["R"] else "Good use of STAR elements.")
    else:
        improvement_suggestions.append("You explained the situation, task, action, and result well.")
    if rel < 1.0:
        improvement_suggestions.append("Connect your answer more directly to the job description skills like Python, REST APIs, etc.")
    if detail < 0.7:
        improvement_suggestions.append("Add more details, examples, and metrics to strengthen your response.")
    if score >= 4.0:
        improvement_suggestions.append("Excellent answer! Well-structured, relevant, and detailed.")
    elif score >= 2.8:
        improvement_suggestions.append("Good effort. Focus on the suggestions above to improve further.")
    else:
        improvement_suggestions.append("This answer needs significant improvement. Review the STAR method and job description requirements.")

    feedback_str = f"Feedback:\n\nScore: {score:.2f} / 5\n\nConfidence Level: {conf.capitalize()}\n\nSTAR Coverage: {star_coverage}\n\nImprovement Suggestions:\n"
    for sug in improvement_suggestions:
        feedback_str += f"• {sug}\n"

    rec = {
        "question_id": q["id"],
        "user_answer": ans,
        "score": score,
        "confidence": conf,
        "star_usage": star,
        "feedback": feedback_str, # Store the detailed feedback string
        "time_taken_sec": time.time() - state["start_time"]
    }

    update = {
        "answers": state["answers"] + [rec],
        "awaiting_answer": False,
        "should_follow_up": False,
    }

    # Difficulty adjustment
    current_difficulty = state["difficulty"]
    if score >= 4.2:
        if current_difficulty == "easy":
            update["difficulty"] = "medium"
        elif current_difficulty == "medium":
            update["difficulty"] = "hard"
    elif score < 3.0:
        if current_difficulty == "hard":
            update["difficulty"] = "medium"
        elif current_difficulty == "medium":
            update["difficulty"] = "easy"

    # Decide if a follow-up is warranted
    if 2.8 <= score < 4.2:
        update["should_follow_up"] = True

    return update

def update_progress(state: InterviewState) -> dict:
    ans = state["answers"]
    if not ans: return {}
    
    last_answer_time_sec = ans[-1]["time_taken_sec"]
    new_estimated_time = state["estimated_time_used_min"] + (last_answer_time_sec / 60.0)
    avg = sum(a["score"] for a in ans)/len(ans)
    
    return {
        "estimated_time_used_min": new_estimated_time,
        "messages": state.get("messages", []) + [AIMessage(content=f"Progress: {avg:.2f}/5 avg score.")]
    }

def controller(state: InterviewState) -> str:
    if state.get("interview_complete"):
        if not state.get("salary_negotiation_phase"):
            return "start_salary_negotiation"
        else:
            return "save_progress"
    
    if state.get("should_follow_up", False):
        return "generate_follow_up_question"
    
    # Time budget check
    if state.get("estimated_time_used_min", 0.0) >= state.get("time_budget_min", 15):
        state.setdefault("messages", []).append(AIMessage(content="Time limit reached."))
        return "generate_final_report"

    if state.get("question_counter", 0) >= state.get("max_questions", 5):
        return "generate_final_report"
    
    return "generate_question"

def generate_final_report(state: InterviewState) -> dict:
    answers = state.get("answers", [])
    if not answers:
        report = {
            "total_questions": 0,
            "average_score": "0.00",
            "overall_confidence": "Low",
            "star_coverage": "0%",
            "behavioral_questions": 0,
            "technical_questions": 0,
            "strengths": ["No questions answered."],
            "areas_to_improve": ["Complete the interview to get feedback."],
            "next_steps": ["Try running the interview simulation again."]
        }
    else:
        total_questions = len(answers)
        average_score = sum(a["score"] for a in answers) / total_questions
        average_star_coverage = sum(sum(a["star_usage"].values()) for a in answers) / (total_questions * 4) * 100

        if average_score >= 4.0:
            overall_confidence = "High"
        elif average_score >= 2.8:
            overall_confidence = "Medium"
        else:
            overall_confidence = "Low"

        strengths = []
        areas_to_improve = []

        if average_score >= 4.0:
            strengths.append("Strong overall performance and clear communication.")
        elif average_score < 2.5:
            areas_to_improve.append("Focus on providing more detailed and structured answers.")

        if average_star_coverage > 75:
            strengths.append("Excellent use of the STAR method.")
        else:
            areas_to_improve.append("Work on consistently applying the STAR method (Situation, Task, Action, Result).")

        # Add more specific feedback based on common low scores or missing skills
        low_scoring_answers = [a for a in answers if a['score'] < 3.0]
        if len(low_scoring_answers) > len(answers) / 2:
            areas_to_improve.append("Elaborate more on the results and impact of your actions.")

        report = {
            "total_questions": total_questions,
            "average_score": f"{average_score:.2f}",
            "overall_confidence": overall_confidence,
            "star_coverage": f"{average_star_coverage:.0f}%",
            "behavioral_questions": state.get("behavioral_questions", 0),
            "technical_questions": state.get("technical_questions", 0),
            "strengths": strengths if strengths else ["Good effort, keep practicing."],
            "areas_to_improve": areas_to_improve if areas_to_improve else ["Continue to refine your stories."],
            "next_steps": [
                "Review the feedback for each question to identify patterns.",
                "Prepare 2-3 additional stories using the STAR method for common behavioral questions.",
                "Practice articulating the impact of your work with measurable outcomes."
            ]
        }

    return {
        "final_report": report,
        "interview_complete": True,
        "messages": state.get("messages", []) + [AIMessage(content="Interview complete. Generating final report.")]
    }

def start_salary_negotiation(state: InterviewState) -> dict:
    """Sets the salary negotiation phase flag."""
    return {"salary_negotiation_phase": True}


def negotiate_salary(state: InterviewState) -> dict:
    """Handles the salary negotiation phase."""
    if not state.get("salary_negotiation_phase"):
        return {}

    # Select a salary question
    salary_questions = [q for q in QUESTION_BANK if q["topic"] == "Salary"]
    if not salary_questions:
        return {}
    
    question = salary_questions[0]

    return {
        "current_question": question,
        "start_time": time.time(),
        "awaiting_answer": True,
        "messages": state.get("messages", []) + [AIMessage(content=f"Now, let's discuss salary. {question['text']}")]
    }


def save_progress(state: InterviewState) -> dict:
    log_file = "interview_log.json"

    # Basic serializable version of the state
    serializable_state = {
        "job_description": state.get("job_description"),
        "user_role": state.get("user_role"),
        "final_report": state.get("final_report"),
        "answers": state.get("answers", [])
    }

    try:
        with open(log_file, "r") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append(serializable_state)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)

    return {}

def build_interview_graph():
    w = StateGraph(InterviewState)
    w.add_node("parse_job_description", parse_job_description)
    w.add_node("research_company", research_company)
    w.add_node("analyze_role", analyze_role)
    w.add_node("generate_question", generate_question)
    w.add_node("evaluate_answer", evaluate_answer)
    w.add_node("generate_follow_up_question", generate_follow_up_question)
    w.add_node("update_progress", update_progress)
    w.add_node("generate_final_report", generate_final_report)
    w.add_node("save_progress", save_progress)
    w.add_node("start_salary_negotiation", start_salary_negotiation)
    w.add_node("negotiate_salary", negotiate_salary)

    w.add_edge(START, "parse_job_description")
    w.add_edge("parse_job_description", "research_company")
    w.add_edge("research_company", "analyze_role")

    w.add_edge("generate_question", "evaluate_answer")
    w.add_edge("generate_follow_up_question", "evaluate_answer")
    w.add_edge("negotiate_salary", "evaluate_answer")
    w.add_edge("evaluate_answer", "update_progress")
    w.add_edge("start_salary_negotiation", "negotiate_salary")

    controller_edges = {
        "generate_question": "generate_question",
        "generate_follow_up_question": "generate_follow_up_question",
        "generate_final_report": "generate_final_report",
        "save_progress": "save_progress",
        "start_salary_negotiation": "start_salary_negotiation",
    }

    w.add_conditional_edges("analyze_role", controller, controller_edges)
    w.add_conditional_edges("update_progress", controller, controller_edges)

    w.add_conditional_edges(
        "generate_final_report",
        controller,
        {
            "start_salary_negotiation": "start_salary_negotiation",
            "save_progress": "save_progress",
        }
    )

    w.add_edge("save_progress", END)
    memory = MemorySaver()
    return w.compile(checkpointer=memory)

def print_transcript(final_state: InterviewState):
    """Prints a human-readable transcript of the mock interview and saves a report."""

    print("\n\n" + "="*20 + " Complete Interview Transcript " + "="*20)

    # 1. Job Description Summary
    print("\n" + "="*15 + " Job Summary " + "="*15)
    print(final_state.get("jd_summary", "No job description summary available."))
    print(f"Skills extracted: {', '.join(final_state.get('required_skills', []))}")
    print(f"Soft Skills: {', '.join(final_state.get('soft_skills', []))}")

    # 2. Company Research Summary
    print("\n" + "="*15 + " Company Insights " + "="*15)
    print(final_state.get("company_insights", "No company insights available."))

    # 3. Role Analysis and Competencies
    print("\n" + "="*15 + " Role Analysis & Required Competencies " + "="*15)
    print(final_state.get("role_analysis", "No role analysis available."))
    print("Key Competencies:")
    for comp in final_state.get("competencies", []):
        print(f"- {comp}")

    # 4. Interview Questions and Answers
    print("\n" + "="*15 + " INTERVIEW TRANSCRIPT " + "="*15)
    questions = final_state.get("asked_questions", [])
    answers = {a['question_id']: a for a in final_state.get("answers", [])}

    for i, question in enumerate(questions):
        print(f"\nQUESTION {i+1}:")
        print(question['text'])
        answer_record = answers.get(question['id'])

        if answer_record:
            print(f"\nCandidate Answer: {answer_record['user_answer']}")
            print(f"\n{answer_record['feedback']}")
            print(f"Time Taken: {answer_record['time_taken_sec']:.0f} seconds")
        else:
            print("Candidate Answer: No answer recorded.")

    # 5. Final Report
    print("\n\n" + "-"*20 + " Final Summary " + "-"*20)
    report = final_state.get("final_report")
    if isinstance(report, dict):
        print(f"Total Questions Answered: {report.get('total_questions', 'N/A')}")
        print(f"Average Score: {report.get('average_score', 'N/A')} / 5")
        print(f"Overall Confidence Rating: {report.get('overall_confidence', 'N/A')}")
        print(f"STAR Coverage: {report.get('star_coverage', 'N/A')}")
        print(f"Behavioral Questions Answered: {report.get('behavioral_questions', 'N/A')}")
        print(f"Technical Questions Answered: {report.get('technical_questions', 'N/A')}")

        print("\nStrengths:")
        for strength in report.get("strengths", []):
            print(f"• {strength}")

        print("\nAreas to Improve:")
        for area in report.get("areas_to_improve", []):
            print(f"• {area}")

        print("\nNext Steps for Preparation:")
        for step in report.get("next_steps", []):
            print(f"• {step}")

        # Save the entire transcript to final_report.txt
        try:
            with open("final_report.txt", "w") as f:
                f.write("="*50 + "\n")
                f.write("COMPLETE INTERVIEW TRANSCRIPT\n")
                f.write("="*50 + "\n\n")

                # Job Summary
                f.write("="*15 + " Job Summary " + "="*15 + "\n")
                f.write(final_state.get("jd_summary", "No job description summary available.") + "\n")
                f.write(f"Skills extracted: {', '.join(final_state.get('required_skills', []))}\n")
                f.write(f"Soft Skills: {', '.join(final_state.get('soft_skills', []))}\n\n")

                # Company Insights
                f.write("="*15 + " Company Insights " + "="*15 + "\n")
                f.write(final_state.get("company_insights", "No company insights available.") + "\n\n")

                # Role Analysis
                f.write("="*15 + " Role Analysis & Required Competencies " + "="*15 + "\n")
                f.write(final_state.get("role_analysis", "No role analysis available.") + "\n")
                f.write("Key Competencies:\n")
                for comp in final_state.get("competencies", []):
                    f.write(f"- {comp}\n")
                f.write("\n")

                # Interview Transcript
                f.write("="*15 + " INTERVIEW TRANSCRIPT " + "="*15 + "\n")
                for i, question in enumerate(questions):
                    f.write(f"\nQUESTION {i+1}:\n")
                    f.write(question['text'] + "\n")
                    answer_record = answers.get(question['id'])
                    if answer_record:
                        f.write(f"\nCandidate Answer: {answer_record['user_answer']}\n")
                        f.write(f"\n{answer_record['feedback']}")
                        f.write(f"Time Taken: {answer_record['time_taken_sec']:.0f} seconds\n")
                    else:
                        f.write("Candidate Answer: No answer recorded.\n")

                # Final Summary
                f.write("\n\n" + "-"*20 + " Final Summary " + "-"*20 + "\n")
                f.write(f"Total Questions Answered: {report.get('total_questions', 'N/A')}\n")
                f.write(f"Average Score: {report.get('average_score', 'N/A')} / 5\n")
                f.write(f"Overall Confidence Rating: {report.get('overall_confidence', 'N/A')}\n")
                f.write(f"STAR Coverage: {report.get('star_coverage', 'N/A')}\n")
                f.write(f"Behavioral Questions Answered: {report.get('behavioral_questions', 'N/A')}\n")
                f.write(f"Technical Questions Answered: {report.get('technical_questions', 'N/A')}\n\n")
                f.write("Strengths:\n")
                for strength in report.get("strengths", []):
                    f.write(f"• {strength}\n")
                f.write("\nAreas to Improve:\n")
                for area in report.get("areas_to_improve", []):
                    f.write(f"• {area}\n")
                f.write("\nNext Steps for Preparation:\n")
                for step in report.get("next_steps", []):
                    f.write(f"• {step}\n")
            print("\nComplete interview transcript saved to final_report.txt")
        except Exception as e:
            print(f"\nError saving report to file: {e}")

    else:
        print(report or "No final report generated.")

if __name__ == "__main__":
    app = build_interview_graph()

    config = {"configurable": {"thread_id": "user-1"}}
    init = {
        "job_description": "Backend Python developer experienced in REST APIs, SQL, Docker.",
        "user_role": "Backend Developer",
        "target_company": "FinTechX",
        "max_questions": 5,
        "time_budget_min": 15,
        "messages": []
    }

    # Start the interview
    current_state = app.invoke(init, config=config)

    # Print preparation sections
    print("\n" + "="*20 + " JOB SUMMARY " + "="*20)
    print(current_state.get("jd_summary", "No job description summary available."))
    print(f"Skills extracted: {', '.join(current_state.get('required_skills', []))}")
    print(f"Soft Skills: {', '.join(current_state.get('soft_skills', []))}")

    print("\n" + "="*20 + " COMPANY INSIGHTS " + "="*20)
    print(current_state.get("company_insights", "No company insights available."))

    print("\n" + "="*20 + " ROLE ANALYSIS & REQUIRED COMPETENCIES " + "="*20)
    print(current_state.get("role_analysis", "No role analysis available."))
    print("Key Competencies:")
    for comp in current_state.get("competencies", []):
        print(f"- {comp}")

    print("\n" + "="*20 + " INTERVIEW STARTS NOW " + "="*20)

    while not current_state.get("interview_complete"):
        ai_message = next((m.content for m in reversed(current_state["messages"]) if isinstance(m, AIMessage)), "")
        if ai_message and "progress" not in ai_message.lower() and "generating final report" not in ai_message.lower():
            # Extract question text
            if "Question:" in ai_message:
                question_text = ai_message.split("Question: ")[1]
                print(f"\nQUESTION {current_state.get('question_counter', 1)}:")
                print(question_text)

        if not current_state.get("awaiting_answer"):
            # If the graph is not waiting for an answer, it might be in a transition state.
            # We can invoke it with no input to let it continue.
            current_state = app.invoke(None, config=config)
            continue

        # The graph is waiting for user input
        user_answer = input("\nCandidate Answer: ")
        prev_answers_count = len(current_state.get("answers", []))
        current_state = app.invoke(
            {"messages": [HumanMessage(content=user_answer)]},
            config=config
        )

        # Print immediate feedback if a new answer was evaluated
        if len(current_state.get("answers", [])) > prev_answers_count:
            latest_answer = current_state["answers"][-1]
            print(f"\n{latest_answer['feedback']}")
            print(f"Time Taken: {latest_answer['time_taken_sec']:.0f} seconds")
            print("-"*50)

    # Print the final transcript
    print_transcript(current_state)
