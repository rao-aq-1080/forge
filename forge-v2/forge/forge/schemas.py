from pydantic import BaseModel, Field, field_validator


class ProjectRequest(BaseModel):
    requirement: str = Field(min_length=20, max_length=12000)
    project_name: str = Field(default="AI Generated Project", max_length=100)
    preferred_language: str = "Python"
    additional_context: str = ""
    # Feature toggles per request
    enable_rag: bool = True
    enable_repair_loop: bool = True


class DevelopmentPlan(BaseModel):
    project_title: str
    problem_statement: str
    objectives: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    development_phases: list[str] = Field(default_factory=list)


class Architecture(BaseModel):
    overview: str
    technology_stack: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    data_flow: list[str] = Field(default_factory=list)
    folder_structure: list[str] = Field(default_factory=list)
    security_considerations: list[str] = Field(default_factory=list)


class GeneratedFile(BaseModel):
    path: str
    content: str

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("File path cannot be empty")
        if ".." in v or v.startswith("/") or v.startswith("\\"):
            raise ValueError("Path traversal not allowed")
        if ":" in v:
            raise ValueError("Drive paths not allowed")
        return v.replace("\\", "/")


class CodeBundle(BaseModel):
    summary: str
    files: list[GeneratedFile] = Field(default_factory=list)
    setup_instructions: str = ""


class RepairBundle(CodeBundle):
    fixes_applied: list[str] = Field(default_factory=list)


class TestCase(BaseModel):
    name: str
    description: str
    inputs: str
    expected: str


class QAReport(BaseModel):
    test_strategy: str
    test_cases: list[TestCase] = Field(default_factory=list)
    edge_cases: list[str] = Field(default_factory=list)
    risk_areas: list[str] = Field(default_factory=list)


class ReviewFinding(BaseModel):
    severity: str
    file: str
    line: str
    issue: str
    recommendation: str


class CodeReview(BaseModel):
    summary: str
    bugs: list[ReviewFinding] = Field(default_factory=list)
    security: list[ReviewFinding] = Field(default_factory=list)
    maintainability: list[ReviewFinding] = Field(default_factory=list)
    overall_score: int = 0


# ---- Feature: Token / cost telemetry ----
class AgentUsage(BaseModel):
    agent: str
    stage: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class Telemetry(BaseModel):
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    agents: list[AgentUsage] = Field(default_factory=list)

    def add(self, usage: AgentUsage) -> None:
        self.agents.append(usage)
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        self.total_tokens += usage.input_tokens + usage.output_tokens
        self.total_cost_usd += usage.cost_usd

    def to_dict(self) -> dict:
        return self.model_dump()


# ---- Feature: Auto-repair loop ----
class RepairIteration(BaseModel):
    iteration: int
    score_before: int
    score_after: int
    findings_addressed: int
    qa_summary: str = ""
    review_summary: str = ""
    improved: bool = False


# ---- Feature: Project diff viewer ----
class FileDiff(BaseModel):
    path: str
    status: str  # added | removed | modified | unchanged
    additions: int = 0
    deletions: int = 0
    patch: str = ""


class ProjectDiff(BaseModel):
    project_id: str
    base: str  # "approved_snapshot" or project id
    comparison: str
    files: list[FileDiff] = Field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0


# ---- Feature: GitHub export ----
class GitHubExportResult(BaseModel):
    project_id: str
    local_repo: str
    remote_url: str = ""
    pushed: bool = False
    commit_sha: str = ""
