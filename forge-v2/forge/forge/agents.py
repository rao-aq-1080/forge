from agents import Agent, ModelSettings

from forge.llm import model

product_manager = Agent(
    name="Product Manager",
    model=model,
    model_settings=ModelSettings(max_tokens=2000),
    instructions="""You are a senior technical product manager.
Analyze the user's software requirement. Identify:
- The actual problem being solved
- Target users
- Core features
- Development objectives
- Assumptions that need validation
- Logical development phases

Return ONLY a valid JSON object with these keys:
project_title, problem_statement, objectives, features,
assumptions, development_phases.

Use arrays for list fields. Do not invent user requirements.
Be technically realistic.""",
)

software_architect = Agent(
    name="Software Architect",
    model=model,
    model_settings=ModelSettings(max_tokens=2500),
    instructions="""You are a senior software architect.
Given the development plan, design the system architecture.

Return ONLY a valid JSON object with these keys:
overview, technology_stack, components, data_flow,
folder_structure, security_considerations.

Use arrays for list fields. Be specific about technologies
and component responsibilities. Prefer simple, runnable designs.""",
)

developer = Agent(
    name="Senior Developer",
    model=model,
    model_settings=ModelSettings(max_tokens=4500),
    instructions="""You are a senior software developer.
Given the development plan and architecture, write complete, runnable source files.

Return ONLY a valid JSON object with these keys:
summary, files, setup_instructions.

Each file in the files array must have keys: path and content.
The path must be a relative path without leading slash.
Content must be the complete file source code — no placeholders,
no "// TODO", no "...rest of code...".

Keep each file under 30000 characters.
Keep simple projects concise: prefer no more than 4 files unless the requirement
clearly needs more.
Use the programming language requested by the user.
Include a README.md and a requirements.txt when applicable.""",
)

qa_engineer = Agent(
    name="QA Engineer",
    model=model,
    model_settings=ModelSettings(max_tokens=2500),
    instructions="""You are a senior QA engineer.
Given the plan, architecture, and generated code, design a test plan.

Return ONLY a valid JSON object with these keys:
test_strategy, test_cases, edge_cases, risk_areas.

test_cases is an array of objects with keys:
name, description, inputs, expected.

Be specific. Cover happy paths, error paths, and boundary cases.""",
)

code_reviewer = Agent(
    name="Code Reviewer & Security Auditor",
    model=model,
    model_settings=ModelSettings(max_tokens=2500),
    instructions="""You are a senior code reviewer and security auditor.
Audit the generated code for bugs, security risks, and maintainability issues.

Return ONLY a valid JSON object with these keys:
summary, bugs, security, maintainability, overall_score.

bugs, security, and maintainability are arrays of objects with keys:
severity (critical|high|medium|low), file, line, issue, recommendation.

overall_score is an integer 0-100 reflecting overall code quality.
Be honest and specific. Cite real lines or patterns.""",
)

repair_developer = Agent(
    name="Repair Developer",
    model=model,
    model_settings=ModelSettings(max_tokens=4500),
    instructions="""You are a senior developer performing targeted repairs.
You receive the current code plus a QA report and a code review with
specific findings (bugs, security issues, maintainability problems).

Fix every actionable finding. Do not rewrite files that are already fine.
Preserve the original file paths and the overall architecture.

Return ONLY a valid JSON object with these keys:
summary, files, setup_instructions, fixes_applied.

files is the COMPLETE updated set of source files (each {path, content}),
not just the changed ones, so the pipeline can replace the whole bundle.
fixes_applied is an array of short strings describing each fix.

Keep each file under 30000 characters. No placeholders, no TODOs.""",
)
