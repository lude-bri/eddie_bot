<a name="readme-top"></a>

<p align="center"> <img src="https://capsule-render.vercel.app/api?type=venom&height=200&color=0ABAB5&text=Eddie42&fontAlign=50&fontAlignY=61&animation=fadeIn&fontColor=fcf3f2&fontSize=100" /> </p>

# About

Eddie42 is a Slack bot designed to interact with 42 Intra API, providing real-time data about students, piscine progress, exams, and campus activity. Built with Python and Slack Bolt, it offers: Student analytics (logtime, project progress, exam results). Piscine monitoring (attrition rates, performance trends). Location tracking (cluster workstation status). Warning system (identifies at-risk students)

-------------------

<ul> <li><strong><a href="#1-architecture" style="color:white">1. Architecture</a></strong></li> <ul style="list-style-type:disc"> 
<li><a href="#11-core-modules">1.1. Core Modules</a></li> 
  <li><a href="#12-data-flow">1.2. Data Flow</a></li> </ul> 
<li><strong><a href="#2-key-features" style="color:white">2. Key Features</a></strong></li> <ul style="list-style-type:disc"> 
<li><a href="#21-slack-commands">2.1. Slack Commands</a></li> 
  <li><a href="#22-warning-system">2.2. Warning System</a></li> </ul> 
<li><strong><a href="#3-setup" style="color:white">3. Setup</a></strong></li> 

---------

# 1. Architecture
## 1.1. Core Modules

| **Module**	| **Purpose** | 
| ---------- | ---------|
| `app/slack_bot.py`	| Handles Slack interactions (commands/events)
`app/api.py`	| Manages 42 Intra API requests (cached)
`app/getters.py`	| Data extraction (logtime, exams, projects)
`app/printer.py`	| Formats responses for Slack
`app/warning.py`	| Flags at-risk students

```mermaid
classDiagram  
    class SlackBot {  
        +handle_commands()  
        +send_messages()  
    }  
    class API {  
        +get_student_data()  
        +get_piscine_data()  
    }  
    SlackBot --> API : Fetches data  
    API --> Getters : Processes raw data  
    Getters --> Printer : Formats output
```
## 1.2. Data Flow

1. Slack Command → slack_bot.py

2. API Call → api.py (cached with requests_cache)

3. Data Processing → getters.py

4. Response Formatting → printer.py


# 2. Key Features
# 2.1. Slack Commands

| Command	| Example | 	Description |
---------- | -------- |------------ |
`_student <login>`	| `_student jdoe`	| Shows student progress
`_piscine <campus> <year> <month>`	| `_piscine porto 2023 september`	| Lists pisciners with filters (warn/care)
`_locate <login/host>` | `_locate c1r1s3`	| Finds a student/cluster host
`_giveup <campus> <dates>`	| `_giveup porto 2023-09-01 2023-09-08`	| Identifies potential dropouts

## 2.2. Warning Systems

**Triggers automated flags:**
  1. **Cheating Risk**: High project scores + low exam performance
  2. **Needs Help**: Missed key projects (e.g., Shell00 in Week 2)

```python
# From warning.py  
if exam_avg > student_exam_avg and project_avg >= 90:  
    return 1  # 🚨 Flag  
elif "C Piscine Shell 00" not in progress_data:  
    return 2  # 🚼 Flag  
```

# 3. Setup

### Requirements
```bash
pip install slack_bolt requests requests-cache  
```
### Environment Variables
```env
SLACK_BOT_TOKEN=xoxb-...  
SLACK_APP_TOKEN=xapp-...  
INTRA_UID=your_uid  
INTRA_SECRET=your_secret  
```

### Run
```bash
python3 main.py  
```
