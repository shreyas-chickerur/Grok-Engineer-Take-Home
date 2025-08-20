import os, json, io, csv
import streamlit as st
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from db import init_db, get_session, Lead, Interaction
from grok_client import GrokClient
from prompts import QUALIFICATION_SYSTEM, QUALIFICATION_USER, OUTREACH_SYSTEM, OUTREACH_USER, fill
from evals import run_table
import re

st.set_page_config(page_title="xAI Take Home Interview", layout="wide")
st.title("Lead Qualification & Outreach")

init_db()
client = GrokClient()

def create_lead(session, **kwargs):
    lead = Lead(**kwargs)
    session.add(lead)
    session.commit()
    return lead

def list_leads(session):
    stmt = select(Lead).order_by(Lead.created_at.desc())
    return session.execute(stmt).scalars().all()

def add_interaction(session, lead_id: int, kind: str, content: str):
    ia = Interaction(lead_id=lead_id, kind=kind, content=content)
    session.add(ia)
    session.commit()

def qualify_lead(session, lead: Lead):
    user_prompt = fill(QUALIFICATION_USER, {
        "name": lead.name, "title": lead.title or "", "company": lead.company or "",
        "website": lead.website or "", "linkedin": lead.linkedin or "", "notes": lead.notes or ""})
    resp = client.chat(QUALIFICATION_SYSTEM, user_prompt)
    parsed = client.parse_json_content(resp)
    if "score" in parsed:
        lead.score = int(parsed["score"])
        session.commit()
    add_interaction(session, lead.id, "qualification", json.dumps(parsed))
    return parsed

def generate_outreach(session, lead: Lead, channel: str, tone: str, value_prop: str):
    tags = []
    rationale = ""
    last_q = session.query(Interaction).filter_by(lead_id=lead.id, kind="qualification").order_by(Interaction.created_at.desc()).first()
    if last_q:
        try:
            q = json.loads(last_q.content)
            tags = q.get("tags", [])
            rationale = q.get("rationale", "")
        except Exception:
            pass
    user_prompt = fill(OUTREACH_USER, {
        "name": lead.name, "title": lead.title or "", "company": lead.company or "",
        "tags": ", ".join(tags), "rationale": rationale, "channel": channel, "tone": tone, "value_prop": value_prop
    })
    resp = client.chat(OUTREACH_SYSTEM, user_prompt)
    parsed = client.parse_json_content(resp)
    add_interaction(session, lead.id, "outreach", json.dumps(parsed))
    return parsed

with st.sidebar:
    st.header("➕ Add Lead")
    with st.form("add_lead"):
        name = st.text_input("Name*", placeholder="Pat Lee", key="name")
        email = st.text_input("Email", placeholder="pat@acme.com")
        company = st.text_input("Company", placeholder="Acme Inc.")
        title = st.text_input("Title", placeholder="VP Engineering")
        website = st.text_input("Website", placeholder="https://acme.com")
        linkedin = st.text_input("LinkedIn", placeholder="https://linkedin.com/in/pat")
        notes = st.text_area("Notes", placeholder="Met at SaaS conference...")
        submitted = st.form_submit_button("Create Lead")
    if submitted and name.strip():
        if " " not in name.strip() or not name:
            st.error("Name must include first and last name (with a space).")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("Please enter a valid email address.")
        elif website and not website.startswith(("http://", "https://")):
            st.error("Website must start with http:// or https://")
        elif linkedin and not re.match(r"^https://(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?$", linkedin):
            st.error("LinkedIn must be a valid profile link (e.g., https://linkedin.com/in/<username>)")
        else:
            with get_session() as s:
                create_lead(s, name=name.strip(), email=email or None, company=company or None,
                            title=title or None, website=website or None, linkedin=linkedin or None, notes=notes or None)
            st.success(f"Lead '{name}' created.")

    st.divider()
    st.caption("🔐 Grok API Key " + ("(dry-run mode)" if client.dry_run else "loaded"))

tab_list = st.tabs(["📋 Leads", "🧪 Evals", "⚙️ Settings"])

with tab_list[0]:
    st.subheader("Leads")
    with get_session() as s:
        leads = list_leads(s)
        if not leads:
            st.info("No leads yet. Add one from the sidebar.")
        else:
            cols = st.columns([2,2,2,2,1,1])
            cols[0].markdown("**Name**")
            cols[1].markdown("**Company**")
            cols[2].markdown("**Title**")
            cols[3].markdown("**Email**")
            cols[4].markdown("**Score**")
            cols[5].markdown("**Actions**")
            for lead in leads:
                c = st.columns([2,2,2,2,1,1])
                c[0].write(lead.name)
                c[1].write(lead.company or "—")
                c[2].write(lead.title or "—")
                c[3].write(lead.email or "—")
                c[4].write(lead.score if lead.score is not None else "—")
                view = c[5].button("Open", key=f"open-{lead.id}")
                if view:
                    st.session_state["open_lead"] = lead.id

    open_id = st.session_state.get("open_lead")
    if open_id:
        with get_session() as s:
            lead = s.get(Lead, open_id)
            if lead:
                st.markdown("---")
                st.subheader(f"Lead: {lead.name}")
                left, right = st.columns([2,1])
                with left:
                    st.write(f"**Company:** {lead.company or '—'}")
                    st.write(f"**Title:** {lead.title or '—'}")
                    st.write(f"**Website:** {lead.website or '—'}")
                    st.write(f"**LinkedIn:** {lead.linkedin or '—'}")
                    st.write(f"**Notes:** {lead.notes or '—'}")
                    st.write(f"**Stage:** {lead.stage}")
                    st.write(f"**Score:** {lead.score if lead.score is not None else '—'}")
                with right:
                    if st.button("⚖️ Qualify Lead"):
                        with get_session() as s2:
                            lead2 = s2.get(Lead, open_id)
                            result = qualify_lead(s2, lead2)
                        st.success("Qualification completed.")
                        st.json(result)
                    st.markdown("**Generate Outreach**")
                    channel = st.selectbox("Channel", ["email", "linkedin", "twitter"], index=0, key="channel")
                    tone = st.selectbox("Tone", ["friendly", "professional", "concise"], index=1, key="tone")
                    value_prop = st.text_input("Value Prop", "Automate SDR tasks with Grok-powered workflows.")
                    if st.button("✉️ Generate Message"):
                        with get_session() as s2:
                            lead2 = s2.get(Lead, open_id)
                            msg = generate_outreach(s2, lead2, channel, tone, value_prop)
                        st.success("Message generated.")
                        st.json(msg)

                st.markdown("### Activity")
                with get_session() as s3:
                    acts = s3.query(Interaction).filter_by(lead_id=open_id).order_by(Interaction.created_at.desc()).all()
                    if acts:
                        for a in acts:
                            st.write(f"- **{a.kind}** · {a.created_at:%Y-%m-%d %H:%M} UTC")
                            with st.expander("View"):
                                st.code(a.content, language="json")
                    else:
                        st.caption("No activity yet.")

with tab_list[1]:
    st.subheader("Prompt Evals")
    st.caption("Run a small sweep against sample leads and compare outputs + latency.")
    samples = [
        {"name":"Riley Chen","title":"Head of Data","company":"NimbusAI","website":"https://nimbus.ai","linkedin":"","notes":"Hiring 3 MLEs; recent funding."},
        {"name":"Jordan Patel","title":"CTO","company":"FleetOps","website":"https://fleetops.io","linkedin":"","notes":"Series B; heavy outbound."},
    ]
    channel = st.selectbox("Channel", ["email","linkedin"], index=0, key="eval_channel")
    tone = st.selectbox("Tone", ["professional","friendly"], index=0, key="eval_tone")
    value_prop = st.text_input("Eval Value Prop", "Book 2x more meetings with assisted outreach.")

    def one(item):
        class Obj: pass
        o = Obj()
        for k,v in item.items(): setattr(o,k,v)
        with get_session() as s:
            lead = Lead(name=o.name, title=o.title, company=o.company, website=o.website, linkedin=o.linkedin, notes=o.notes)
            s.add(lead); s.commit()
            q = qualify_lead(s, lead)
            m = generate_outreach(s, lead, channel, tone, value_prop)
        return {"qualification": q, "message": m}

    if st.button("Run Eval on Samples"):
        rows = run_table(samples, one)
        for row in rows:
            st.write(f"### Sample {row['idx']} (latency: {row['latency_s']}s)")
            st.json(row["output"])

with tab_list[2]:
    st.subheader("Settings & Utilities")
    colA, colB = st.columns(2)
    with colA:
        st.write("**Export Leads**")
        if st.button("Download CSV"):
            from sqlalchemy import select
            with get_session() as s:
                rows = s.execute(select(Lead)).scalars().all()
                output = io.StringIO()
                w = csv.writer(output)
                w.writerow(["id","name","email","company","title","website","linkedin","notes","score","stage","created_at"])
                for r in rows:
                    w.writerow([r.id,r.name,r.email or "",r.company or "",r.title or "",r.website or "",r.linkedin or "",(r.notes or "").replace("\n"," "),r.score if r.score is not None else "", r.stage, r.created_at.isoformat()])
                st.download_button("Save leads.csv", data=output.getvalue(), file_name="leads.csv", mime="text/csv")
    with colB:
        st.write("**Danger Zone**")
        if st.button("Clear All Data"):
            from sqlalchemy import text
            with get_session() as s:
                s.execute(delete(Interaction))
                s.execute(delete(Lead))
                s.commit()
            st.warning("Database cleared.")
