#!/usr/bin/env python3
"""
Bensley AI Crew - Autonomous Coordination System
Coordinates Claude (backend) and Codex (frontend) autonomously
"""

import os
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# Set up AI models
claude_llm = ChatOpenAI(
    model="claude-3-5-sonnet-20241022",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    base_url="https://api.anthropic.com/v1"
)

codex_llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Define Claude Agent (Backend)
claude_agent = Agent(
    role='Backend Engineer & Database Specialist',
    goal='Build FastAPI endpoints, database schemas, Python scripts, and data pipelines for Bensley',
    backstory="""You are Claude, the backend specialist for Bensley Design Studios.
    You build APIs, manage databases, write Python scripts, and handle all data infrastructure.
    You work closely with Codex (frontend) to ensure APIs match UI needs.

    Key responsibilities:
    - Database design and migrations
    - FastAPI endpoint development
    - Data quality and integrity
    - AI/ML integration for document processing
    - Performance optimization

    Communication style: Technical, precise, proactive about potential issues.
    Always propose API contracts before building so frontend knows what to expect.""",
    verbose=True,
    allow_delegation=True,
    llm=claude_llm
)

# Define Codex Agent (Frontend/Product)
codex_agent = Agent(
    role='Frontend Engineer & Product Designer',
    goal='Build Next.js UI, design user workflows, and ensure great UX for Bensley',
    backstory="""You are Codex, the frontend and product specialist for Bensley Design Studios.
    You build React/Next.js dashboards, design workflows, and think about user experience.
    You work closely with Claude (backend) to coordinate on features.

    Key responsibilities:
    - Next.js dashboard development
    - UI/UX design and user workflows
    - API contract specification
    - Product thinking and feature prioritization
    - Integration with backend APIs

    Communication style: User-focused, design-conscious, pragmatic.
    Always think "will this actually help Bill/Brian?" before building.""",
    verbose=True,
    allow_delegation=True,
    llm=codex_llm
)

def create_database_intelligence_crew(user_goal):
    """
    Create a crew to build the database intelligence system
    WORKFLOW: Plan together → Discuss → Agree → Build → Integrate
    """

    # PHASE 1: CODEX PROVIDES INITIAL GUIDANCE (High-level thinking)
    initial_planning_task = Task(
        description=f"""
        USER'S GOAL: {user_goal}

        As the product/UX specialist, provide INITIAL HIGH-LEVEL GUIDANCE on this vision.

        Your responsibilities:
        1. **Product Thinking:** Is this the right approach? Better alternatives?
        2. **User Workflow:** How should the user interact with this system?
        3. **UX Design:** What's the best way to review 100+ suggestions?
        4. **Information Architecture:** What evidence should we show? How to prioritize?
        5. **Concerns:** What could go wrong? What's risky?

        Questions to answer:
        - Is suggestion-based review the right UX? Or should we do something else?
        - One-by-one review? Batch? Auto-apply with thresholds?
        - How to make this fast (10-15 min) not slow (hours)?
        - What makes training data actually useful for future LLM?
        - Is this solving the real problem (database quality)?

        **BE CRITICAL:** If you see a better approach, propose it!
        Don't just rubber-stamp the idea. Think about what's BEST for Bill/Brian.

        Output:
        - Your high-level product vision
        - Proposed UX workflow
        - Concerns and risks
        - Alternative approaches if you see better ones
        - What you need from Claude (backend)
        """,
        agent=codex_agent,
        expected_output="High-level product plan with UX vision and critical analysis"
    )

    # PHASE 2: CLAUDE REVIEWS AND PROVIDES TECHNICAL FEEDBACK
    technical_review_task = Task(
        description=f"""
        Review Codex's product plan and provide TECHNICAL FEEDBACK.

        Your responsibilities:
        1. **Technical Feasibility:** Can we build what Codex proposed?
        2. **Data Reality:** What patterns can we actually detect?
        3. **Confidence Scoring:** How accurate can we be?
        4. **Performance:** Can we process 153 projects quickly?
        5. **Concerns:** Technical risks, data quality issues

        Questions to answer:
        - Is Codex's UX technically feasible?
        - What can we detect with high confidence (>90%)?
        - What's hard to detect reliably?
        - Database schema changes needed?
        - API complexity vs UX needs?

        **BE HONEST:** If something is harder than Codex thinks, say so!
        Propose technical alternatives if you see better ways.

        Output:
        - Technical feasibility assessment
        - What you can build with high confidence
        - What's risky/hard
        - Proposed backend architecture
        - API contract suggestions
        - Concerns about Codex's plan (if any)
        """,
        agent=claude_agent,
        expected_output="Technical review with feasibility assessment and architecture proposal"
    )

    # PHASE 3: COLLABORATIVE REFINEMENT (Both discuss and agree)
    collaborative_planning_task = Task(
        description="""
        COLLABORATE to finalize the best approach.

        Both agents discuss:
        1. **Resolve differences:** If you disagree, work it out
        2. **Refine the plan:** Combine product vision + technical reality
        3. **Agree on approach:** UX workflow + Backend architecture
        4. **API contract:** Exact endpoints, payloads, responses
        5. **Success criteria:** How do we know it's working?

        Discussion points:
        - Codex: Is Claude's architecture going to support your UX?
        - Claude: Is Codex's UX asking for things we can't deliver?
        - Both: What's the MVP? What's nice-to-have?
        - Both: What could go wrong? How to mitigate?

        **RESULT:** Unified plan that both agents agree is BEST.

        Output:
        - Final agreed approach
        - UX workflow (Codex approved)
        - Backend architecture (Claude approved)
        - API contract (both agreed)
        - Build plan with clear division of work
        - Risk mitigation strategy
        """,
        agent=codex_agent,
        expected_output="Unified plan agreed by both agents, ready for user approval"
    )

    # PHASE 4: BUILD BACKEND (Claude's complex coding work)
    backend_build_task = Task(
        description="""
        Build the backend audit system based on the AGREED PLAN.

        Only start after plan is finalized!

        Your tasks:
        1. Build ai_database_auditor.py with pattern detection
        2. Implement confidence scoring system
        3. Create API endpoints per agreed contract
        4. Set up training data logging
        5. Test with real database data
        6. Document API for Codex

        Focus on:
        - High-quality pattern detection
        - Accurate confidence scores
        - Clean API design
        - Performance (should be fast)

        Output:
        - Working audit system
        - API endpoints live and tested
        - Documentation for Codex
        - Sample suggestions ready
        """,
        agent=claude_agent,
        expected_output="Working backend system matching agreed plan"
    )

    # PHASE 5: BUILD FRONTEND (Codex's UX work)
    frontend_build_task = Task(
        description="""
        Build the suggestion review UI based on the AGREED PLAN.

        Only start after Claude's API is ready!

        Your tasks:
        1. Build suggestion review interface
        2. Implement approval workflow
        3. Display evidence and confidence scores
        4. Connect to Claude's API endpoints
        5. Test end-to-end flow

        Focus on:
        - Fast review workflow (user can finish in 10-15 min)
        - Clear evidence display
        - Smooth approval process
        - Training data collection

        Output:
        - Working UI connected to backend
        - Tested approval workflow
        - Ready for user testing
        """,
        agent=codex_agent,
        expected_output="Working frontend matching agreed plan"
    )

    # PHASE 6: INTEGRATION & TESTING
    integration_task = Task(
        description="""
        Final integration and testing.

        Both agents verify:
        1. End-to-end flow works
        2. API integration is solid
        3. Training data logs correctly
        4. Performance is good
        5. Edge cases handled

        Final deliverable:
        - Complete working system
        - Tested and verified
        - Ready for user
        - Documentation complete
        """,
        agent=claude_agent,
        expected_output="Fully integrated system ready for user testing"
    )

    # Create crew with proper planning workflow
    crew = Crew(
        agents=[claude_agent, codex_agent],
        tasks=[
            initial_planning_task,      # Codex: High-level guidance
            technical_review_task,      # Claude: Technical feedback
            collaborative_planning_task,# Both: Discuss and agree
            backend_build_task,         # Claude: Build complex code
            frontend_build_task,        # Codex: Build UI
            integration_task            # Both: Integrate and test
        ],
        process=Process.sequential,  # Must go in order (plan before build!)
        verbose=True
    )

    return crew

def simple_coordination(user_request):
    """
    Simple coordination between Claude and Codex on any request
    """

    planning_task = Task(
        description=f"""
        User request: {user_request}

        Break this down into:
        1. Backend work needed
        2. Frontend work needed
        3. Integration points
        4. Suggest division of labor between you and Codex
        """,
        agent=claude_agent,
        expected_output="Work breakdown with backend/frontend division"
    )

    implementation_plan_task = Task(
        description=f"""
        Based on Claude's breakdown, design the UX and workflow.

        User request: {user_request}

        Your tasks:
        1. Review Claude's backend plan
        2. Design the user-facing workflow
        3. Specify what you need from backend APIs
        4. Propose timeline and milestones
        """,
        agent=codex_agent,
        expected_output="Frontend plan with API requirements"
    )

    crew = Crew(
        agents=[claude_agent, codex_agent],
        tasks=[planning_task, implementation_plan_task],
        process=Process.sequential,
        verbose=True
    )

    return crew

if __name__ == "__main__":
    print("=" * 80)
    print("BENSLEY AI CREW - AUTONOMOUS COORDINATION")
    print("=" * 80)

    # Example usage
    user_goal = """
    Build an AI-powered database intelligence system that:
    1. Audits all 153 projects and detects status issues
    2. Makes confidence-scored suggestions for fixes
    3. Lets me approve/reject suggestions via UI
    4. Logs all decisions to training_data for future local LLM
    5. Learns patterns like: "13 BK = 2013 = old project"
    """

    print("\nCreating crew for database intelligence system...")
    crew = create_database_intelligence_crew(user_goal)

    print("\nStarting autonomous coordination...")
    print("Claude and Codex will now work together autonomously!\n")

    # Run the crew
    result = crew.kickoff()

    print("\n" + "=" * 80)
    print("COORDINATION COMPLETE!")
    print("=" * 80)
    print("\nResult:")
    print(result)
