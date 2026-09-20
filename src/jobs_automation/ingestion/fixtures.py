"""Sample fixtures for job alerts, recruiting emails, and thread tracking."""

from __future__ import annotations

import datetime

from jobs_automation.ingestion.models import RawEmailMessage


def get_sample_email_fixtures() -> list[RawEmailMessage]:
    now = datetime.datetime.now(datetime.UTC)
    t0 = now - datetime.timedelta(hours=6)
    t1 = now - datetime.timedelta(hours=5)
    t2 = now - datetime.timedelta(hours=4)
    t3 = now - datetime.timedelta(hours=3)
    t4 = now - datetime.timedelta(hours=2)
    t5 = now - datetime.timedelta(hours=1)

    # 1. LinkedIn Job Alert Email
    linkedin_html = """
    <html>
      <body>
        <h2>Top job picks for you</h2>
        <table>
          <tr>
            <td>
              <a href="https://www.linkedin.com/jobs/view/4100112233?trk=eml-jobs-alert&refId=abc1234">
                Enterprise Automation Architect
              </a>
              <div>Viatris Global</div>
              <div>Pittsburgh, PA (Hybrid)</div>
              <div>$165,000 - $195,000/yr</div>
            </td>
          </tr>
          <tr>
            <td>
              <a href="https://www.linkedin.com/jobs/view/4100112234?trk=eml-jobs-alert">
                SAP BTP Solutions Architect
              </a>
              <div>Accenture</div>
              <div>Remote - United States</div>
              <div>$170,000 - $205,000/yr</div>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """
    msg_linkedin = RawEmailMessage(
        provider_message_id="gmail_alert_linkedin_001",
        provider_thread_id="thread_alert_linkedin",
        received_at=t0,
        sender="jobalerts-noreply@linkedin.com",
        recipients=["priyansh.chordia@gmail.com"],
        direction="inbound",
        subject="Priyansh, 2 new jobs for 'Enterprise Automation Architect'",
        headers={"Message-ID": "gmail_alert_linkedin_001"},
        body_text="Top job picks for you: Enterprise Automation Architect at Viatris Global",
        body_html=linkedin_html,
    )

    # 2. Indeed Job Alert Email
    indeed_html = """
    <html>
      <body>
        <h2>Indeed Job Alert: AI Automation Engineer</h2>
        <table>
          <tr>
            <td>
              <a href="https://www.indeed.com/viewjob?jk=a1b2c3d4e5f6&from=ja&tk=12345">
                Senior AI Automation Engineer
              </a>
              <div>Cresta AI</div>
              <div>Remote</div>
              <div>$160,000 - $190,000 a year</div>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """
    msg_indeed = RawEmailMessage(
        provider_message_id="gmail_alert_indeed_001",
        provider_thread_id="thread_alert_indeed",
        received_at=t1,
        sender="alert@indeed.com",
        recipients=["priyansh.chordia@gmail.com"],
        direction="inbound",
        subject="Indeed Job Alert: AI Automation Engineer",
        headers={"Message-ID": "gmail_alert_indeed_001"},
        body_text="Senior AI Automation Engineer at Cresta AI",
        body_html=indeed_html,
    )

    # 3. ZipRecruiter Job Alert Email
    zip_html = """
    <html>
      <body>
        <h2>New Job Match</h2>
        <div>
          <a href="https://www.ziprecruiter.com/job/zr_987654321?utm_source=alert&trk=123">
            Principal Solutions Architect
          </a>
          <div>Databricks</div>
          <div>Remote, US</div>
          <div>$180,000 - $220,000/year</div>
        </div>
      </body>
    </html>
    """
    msg_zip = RawEmailMessage(
        provider_message_id="gmail_alert_zip_001",
        provider_thread_id="thread_alert_zip",
        received_at=t2,
        sender="jobalerts@ziprecruiter.com",
        recipients=["priyansh.chordia@gmail.com"],
        direction="inbound",
        subject="ZipRecruiter Job Match: Principal Solutions Architect",
        headers={"Message-ID": "gmail_alert_zip_001"},
        body_text="Principal Solutions Architect at Databricks",
        body_html=zip_html,
    )

    # 4. Dice Tech Job Alert Email
    dice_html = """
    <html>
      <body>
        <h2>Dice Daily Tech Jobs</h2>
        <div>
          <a href="https://www.dice.com/job-detail/dice_job_555?utm_source=dice_alert">
            SAP Integration & Automation Lead
          </a>
          <div>Siemens Enterprise</div>
          <div>Pittsburgh, PA</div>
          <div>$155,000 - $185,000</div>
        </div>
      </body>
    </html>
    """
    msg_dice = RawEmailMessage(
        provider_message_id="gmail_alert_dice_001",
        provider_thread_id="thread_alert_dice",
        received_at=t3,
        sender="jobs@dice.com",
        recipients=["priyansh.chordia@gmail.com"],
        direction="inbound",
        subject="Dice Job Alert: SAP Integration & Automation Lead",
        headers={"Message-ID": "gmail_alert_dice_001"},
        body_text="SAP Integration & Automation Lead at Siemens Enterprise",
        body_html=dice_html,
    )

    # 5. Inbound Recruiter Outreach (Thread A)
    msg_recruiter_in = RawEmailMessage(
        provider_message_id="gmail_recruiter_001",
        provider_thread_id="thread_recruiting_viatrix",
        received_at=t4,
        sender="sarah.connor@viatris.com",
        recipients=["priyansh.chordia@gmail.com"],
        direction="inbound",
        subject="Solutions Architecture Opportunity at Viatris",
        headers={"Message-ID": "gmail_recruiter_001"},
        body_text="Hi Priyansh, I came across your background with SAP BTP and AI automation and was impressed. Are you available for a brief introductory call this week?",
        body_html="<p>Hi Priyansh, I came across your background with SAP BTP and AI automation and was impressed. Are you available for a brief introductory call this week?</p>",
    )

    # 6. Outbound Candidate Reply (Thread A continuation!)
    msg_candidate_out = RawEmailMessage(
        provider_message_id="gmail_candidate_001",
        provider_thread_id="thread_recruiting_viatrix",
        received_at=t5,
        sender="priyansh.chordia@gmail.com",
        recipients=["sarah.connor@viatris.com"],
        direction="outbound",
        subject="Re: Solutions Architecture Opportunity at Viatris",
        headers={"Message-ID": "gmail_candidate_001", "In-Reply-To": "gmail_recruiter_001"},
        body_text="Hi Sarah, thank you for reaching out. Yes, I would be glad to connect. Thursday afternoon works well for me.",
        body_html="<p>Hi Sarah, thank you for reaching out. Yes, I would be glad to connect. Thursday afternoon works well for me.</p>",
    )

    # 7. Application Confirmation (Different Company)
    msg_confirmation = RawEmailMessage(
        provider_message_id="gmail_conf_001",
        provider_thread_id="thread_app_cresta",
        received_at=now,
        sender="no-reply@cresta.ai",
        recipients=["priyansh.chordia@gmail.com"],
        direction="inbound",
        subject="Thank you for applying to Cresta AI",
        headers={"Message-ID": "gmail_conf_001"},
        body_text="Thank you for applying for the AI Automation Engineer position at Cresta AI. We have received your application and will review it shortly.",
        body_html="<p>Thank you for applying for the AI Automation Engineer position at Cresta AI.</p>",
    )

    return [
        msg_linkedin,
        msg_indeed,
        msg_zip,
        msg_dice,
        msg_recruiter_in,
        msg_candidate_out,
        msg_confirmation,
    ]
