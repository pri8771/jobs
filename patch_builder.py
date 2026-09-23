content = open("src/jobs_automation/preparation/packet_builder.py").read()
content = content.replace(
    "variant_name = ResumeVariantSelector.select_variant(job, matched_role_family)",
    "variant_name = ResumeVariantSelector.select_variant(job, matched_role_family, session=self.session, config=self.config)"
)
with open("src/jobs_automation/preparation/packet_builder.py", "w") as f:
    f.write(content)
