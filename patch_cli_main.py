import sys

content = open("src/jobs_automation/cli/main.py").read()

old_code = """    loader = ConfigLoader(config_dir)
    profile, _ = loader.load_candidate_profile()

    from sqlalchemy import select"""

new_code = """    loader = ConfigLoader(config_dir)
    profile, _ = loader.load_candidate_profile()
    search_config, _ = loader.load_job_search_config()

    from sqlalchemy import select"""

content = content.replace(old_code, new_code)

old_builder = """        builder = ApplicationPacketBuilder(
            session=session,
            candidate_profile=profile,
            model_gateway=MockModelGateway(),
        )"""

new_builder = """        builder = ApplicationPacketBuilder(
            session=session,
            candidate_profile=profile,
            model_gateway=MockModelGateway(),
            config=search_config,
        )"""

content = content.replace(old_builder, new_builder)

with open("src/jobs_automation/cli/main.py", "w") as f:
    f.write(content)
