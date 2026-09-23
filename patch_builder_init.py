import re

content = open("src/jobs_automation/preparation/packet_builder.py").read()

if "from jobs_automation.core.job_search import JobSearchConfig" not in content:
    content = "from jobs_automation.core.job_search import JobSearchConfig\n" + content

init_old = """    def __init__(
        self,
        session: Session,
        candidate_profile: CandidateProfileConfig,
        model_gateway: ModelGateway,
        artifact_store: ArtifactStore | None = None,
    ) -> None:
        self.session = session
        self.profile = candidate_profile
        self.gateway = model_gateway
        self.artifact_store = artifact_store or ArtifactStore("artifacts")
        self.cover_letter_drafter = CoverLetterDrafter(model_gateway)
        self.question_service = ScreeningQuestionAnsweringService(model_gateway)"""

init_new = """    def __init__(
        self,
        session: Session,
        candidate_profile: CandidateProfileConfig,
        model_gateway: ModelGateway,
        artifact_store: ArtifactStore | None = None,
        config: JobSearchConfig | None = None,
    ) -> None:
        self.session = session
        self.profile = candidate_profile
        self.gateway = model_gateway
        self.artifact_store = artifact_store or ArtifactStore("artifacts")
        self.cover_letter_drafter = CoverLetterDrafter(model_gateway)
        self.question_service = ScreeningQuestionAnsweringService(model_gateway)
        self.config = config"""

content = content.replace(init_old, init_new)

with open("src/jobs_automation/preparation/packet_builder.py", "w") as f:
    f.write(content)
