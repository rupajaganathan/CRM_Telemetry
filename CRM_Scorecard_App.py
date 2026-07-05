"""
CRM Scorecard App
Ascend Together | CRM Program

Tracks the 10 net-new metrics not covered by existing reports.
Upload CSVs from your CRM export, or run in demo mode with sample data.

Required CSVs (see sidebar for column specs):
  - opportunities.csv
  - stage_history.csv
  - tasks.csv
  - activities.csv
  - referrals.csv
  - users.csv

Run: streamlit run CRM_Scorecard_App.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date, timedelta
import random

# ─── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="CRM Scorecard | Ascend Together",
    page_icon="📊",
    layout="wide",
)

# ─── Styling ───────────────────────────────────────────────────────────
st.markdown("""
<style>
  .metric-card {
    background: #f8f9fb;
    border-left: 4px solid #2E75B6;
    border-radius: 6px;
    padding: 16px 20px;
    margin-bottom: 12px;
  }
  .metric-label { font-size: 13px; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  .metric-value { font-size: 32px; font-weight: 700; color: #1F3864; margin: 4px 0; }
  .metric-sub   { font-size: 13px; color: #888; }
  .section-head { font-size: 18px; font-weight: 700; color: #2E75B6;
                  border-bottom: 2px solid #D6E4F0; padding-bottom: 6px; margin: 24px 0 16px 0; }
  .status-green  { color: #1a7f37; font-weight: 600; }
  .status-amber  { color: #b45309; font-weight: 600; }
  .status-red    { color: #b91c1c; font-weight: 600; }
  .demo-banner   { background: #fff7ed; border: 1px solid #fed7aa; border-radius: 6px;
                   padding: 10px 16px; margin-bottom: 20px; color: #9a3412; font-size: 14px; }
  .data-note     { font-size: 11px; color: #aaa; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ─── Demo data generator ───────────────────────────────────────────────
@st.cache_data
def generate_demo_data():
    random.seed(42)
    np.random.seed(42)
    today = date.today()
    firms = ["ATKG", "Windham", "TSA", "Summit CPA"]
    stages = ["Initial Contact", "Discovery", "Proposal Sent", "Negotiation", "Verbal Agreement", "Closed Won", "Closed Lost"]
    stage_days = {"Initial Contact": 8, "Discovery": 14, "Proposal Sent": 12,
                  "Negotiation": 10, "Verbal Agreement": 6, "Closed Won": 2, "Closed Lost": 2}

    # Opportunities
    opps = []
    for i in range(120):
        firm = random.choice(firms)
        created = today - timedelta(days=random.randint(10, 300))
        opp_type = random.choice(["New Business"] * 2 + ["Client Expansion"])
        outcome = random.choices(["Open", "Won", "Lost", "On-Hold"], weights=[40, 35, 20, 5])[0]
        closed = None
        if outcome in ("Won", "Lost"):
            closed = created + timedelta(days=random.randint(30, 120))
            if closed > today:
                closed = today
        opps.append({
            "opportunity_id": f"OPP-{1000+i}",
            "prospect_id": f"PROS-{200+i%40}",
            "opportunity_type": opp_type,
            "date_created": created,
            "actual_completion_date": closed,
            "outcome": outcome,
            "firm_id": firm,
        })
    opps_df = pd.DataFrame(opps)

    # Stage history
    stage_rows = []
    for _, opp in opps_df.iterrows():
        path = stages[:random.randint(2, len(stages))]
        if opp["outcome"] == "Won":
            path = ["Initial Contact", "Discovery", "Proposal Sent"] + random.sample(["Negotiation", "Verbal Agreement"], k=random.randint(0,1)) + ["Closed Won"]
        elif opp["outcome"] == "Lost":
            path = ["Initial Contact", "Discovery"] + random.sample(["Proposal Sent", "Negotiation"], k=random.randint(1,2)) + ["Closed Lost"]
        elif opp["outcome"] == "Open":
            path = stages[:random.randint(1, 5)]
        cur = opp["date_created"]
        for j, stg in enumerate(path):
            days = stage_days.get(stg, 10) + random.randint(-3, 10)
            end = cur + timedelta(days=days) if j < len(path)-1 else (opp["actual_completion_date"] or (today - timedelta(days=1)))
            stage_rows.append({
                "opportunity_id": opp["opportunity_id"],
                "stage_name": stg,
                "stage_start_date": cur,
                "stage_end_date": end,
                "firm_id": opp["firm_id"],
            })
            cur = end
    stages_df = pd.DataFrame(stage_rows)

    # Referrals
    refs = []
    for i in range(60):
        firm = random.choice(firms)
        created = today - timedelta(days=random.randint(10, 250))
        has_opp = random.random() < 0.65
        opp_date = created + timedelta(days=random.randint(2, 30)) if has_opp else None
        opp_id = f"OPP-{1000 + random.randint(0,119)}" if has_opp else None
        won = random.random() < 0.45 if has_opp else False
        refs.append({
            "referral_id": f"REF-{500+i}",
            "created_date": created,
            "linked_opportunity_id": opp_id,
            "linked_opportunity_date": opp_date,
            "outcome": ("Won" if won else "Lost" if has_opp and random.random() < 0.3 else "Open" if has_opp else "None"),
            "firm_id": firm,
        })
    refs_df = pd.DataFrame(refs)

    # Tasks
    tasks = []
    for i in range(200):
        firm = random.choice(firms)
        created = today - timedelta(days=random.randint(1, 90))
        due = created + timedelta(days=random.randint(1, 21))
        status = random.choices(["Completed", "Open", "Canceled"], weights=[55, 35, 10])[0]
        created_by = random.choices(["user", "system"], weights=[60, 40])[0]
        comp = due + timedelta(days=random.randint(-3, 5)) if status == "Completed" else None
        tasks.append({
            "task_id": f"TASK-{3000+i}",
            "opportunity_id": f"OPP-{1000+random.randint(0,119)}",
            "status": status,
            "due_date": due,
            "completion_date": comp,
            "created_by": created_by,
            "firm_id": firm,
        })
    tasks_df = pd.DataFrame(tasks)

    # Activities
    acts = []
    for i in range(400):
        firm = random.choice(firms)
        opp_id = f"OPP-{1000+random.randint(0,119)}"
        created_by = random.choices(["user", "system"], weights=[65, 35])[0]
        act_type = random.choices(
            ["Note", "Call", "Meeting", "Email", "Fireflies", "AutoEmail"],
            weights=[20, 20, 15, 15, 15, 15])[0]
        if created_by == "system":
            act_type = random.choice(["Fireflies", "AutoEmail"])
        acts.append({
            "activity_id": f"ACT-{5000+i}",
            "opportunity_id": opp_id,
            "activity_type": act_type,
            "created_by": created_by,
            "created_date": today - timedelta(days=random.randint(0, 90)),
            "firm_id": firm,
        })
    acts_df = pd.DataFrame(acts)

    # Users
    users = []
    uid = 1
    for firm in firms:
        n = random.randint(8, 15)
        for _ in range(n):
            logged_in = random.random() < 0.72
            engaged = random.random() < 0.55 if logged_in else False
            users.append({
                "user_id": f"USR-{uid:03d}",
                "firm_id": firm,
                "role": random.choice(["Partner", "Manager", "Staff"]),
                "logged_in_this_month": logged_in,
                "manually_engaged_this_month": engaged,
            })
            uid += 1
    users_df = pd.DataFrame(users)

    return opps_df, stages_df, refs_df, tasks_df, acts_df, users_df


# ─── CSV loaders with column validation ────────────────────────────────
REQUIRED_COLS = {
    "opportunities": ["opportunity_id","prospect_id","opportunity_type","date_created",
                      "actual_completion_date","outcome","firm_id"],
    "stage_history": ["opportunity_id","stage_name","stage_start_date","stage_end_date","firm_id"],
    "tasks":         ["task_id","opportunity_id","status","due_date","completion_date","created_by","firm_id"],
    "activities":    ["activity_id","opportunity_id","activity_type","created_by","created_date","firm_id"],
    "referrals":     ["referral_id","created_date","linked_opportunity_id","linked_opportunity_date","outcome","firm_id"],
    "users":         ["user_id","firm_id","role","logged_in_this_month","manually_engaged_this_month"],
    "pipeline_summary": ["firm_name","source","intake_pending","opportunity_count","service_line_count","closed_won"],
}

def load_csv(upload, name):
    if upload is None:
        return None
    df = pd.read_csv(upload)
    df.columns = [c.strip().lower().replace(" ","_") for c in df.columns]
    missing = [c for c in REQUIRED_COLS[name] if c not in df.columns]
    if missing:
        st.sidebar.error(f"{name}.csv missing columns: {missing}")
        return None
    return df

def parse_dates(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    return df


# ─── Metric calculation functions ──────────────────────────────────────
today = date.today()

def m1_stage_dwell(stages_df):
    """Average days in each stage."""
    df = stages_df.copy()
    df["start"] = pd.to_datetime(df["stage_start_date"]).dt.date
    df["end"]   = pd.to_datetime(df["stage_end_date"]).dt.date
    df["days"]  = (pd.to_datetime(df["end"]) - pd.to_datetime(df["start"])).dt.days
    df = df[df["days"] >= 0]
    return df.groupby("stage_name")["days"].mean().round(1).sort_values(ascending=False)

def m2_referral_response(refs_df):
    """Avg days from referral created to first opportunity."""
    df = refs_df.dropna(subset=["linked_opportunity_date"]).copy()
    df["created"] = pd.to_datetime(df["created_date"]).dt.date
    df["opp_date"] = pd.to_datetime(df["linked_opportunity_date"]).dt.date
    df["days"] = (pd.to_datetime(df["opp_date"]) - pd.to_datetime(df["created"])).dt.days
    df = df[df["days"] >= 0]
    avg = df["days"].mean()
    gap_pct = (refs_df["linked_opportunity_id"].isna().sum() / len(refs_df) * 100) if len(refs_df) else 0
    return round(avg, 1), round(gap_pct, 1)

def m3_stage_conversion(stages_df, opps_df):
    """% of opportunities that reached each stage."""
    total = len(opps_df)
    if total == 0:
        return pd.Series(dtype=float)
    stage_order = ["Initial Contact","Discovery","Proposal Sent",
                   "Negotiation","Verbal Agreement","Closed Won"]
    reached = {s: stages_df[stages_df["stage_name"]==s]["opportunity_id"].nunique() for s in stage_order}
    pct = {s: round(v/total*100,1) for s,v in reached.items()}
    return pd.Series(pct)

def m4_referral_conversion(refs_df):
    """% referrals resulting in at least one Won opp."""
    total = len(refs_df)
    if total == 0:
        return 0, 0
    won = refs_df[refs_df["outcome"]=="Won"].shape[0]
    has_opp = refs_df[refs_df["linked_opportunity_id"].notna()].shape[0]
    return round(won/total*100,1), round(has_opp/total*100,1)

def m5_task_completion(tasks_df):
    """Completed / (Completed + Open + Canceled)."""
    df = tasks_df[tasks_df["created_by"] == "user"]  # exclude system tasks
    if len(df) == 0:
        return 0
    return round(df[df["status"]=="Completed"].shape[0] / len(df) * 100, 1)

def m6_overdue_tasks(tasks_df):
    """Open tasks past due date %."""
    open_t = tasks_df[tasks_df["status"]=="Open"].copy()
    if len(open_t) == 0:
        return 0
    open_t["due"] = pd.to_datetime(open_t["due_date"]).dt.date
    overdue = open_t[open_t["due"] < today]
    return round(len(overdue)/len(open_t)*100, 1)

def m7_opps_ytd(opps_df):
    """Opportunities created YTD."""
    df = opps_df.copy()
    df["created"] = pd.to_datetime(df["date_created"]).dt.date
    ytd = df[df["created"].apply(lambda d: d.year if d else 0) == today.year]
    return len(ytd)

def m8_activities_per_opp(acts_df, opps_df):
    """Avg user-initiated activities per closed opportunity (excl. system-generated)."""
    user_acts = acts_df[
        (acts_df["created_by"]=="user") &
        (~acts_df["activity_type"].isin(["Fireflies","AutoEmail"]))
    ]
    closed = opps_df[opps_df["outcome"].isin(["Won","Lost"])]
    if len(closed) == 0:
        return 0
    counts = user_acts.groupby("opportunity_id").size()
    matched = counts.reindex(closed["opportunity_id"], fill_value=0)
    return round(matched.mean(), 1)

def m9_login_rate(users_df):
    """% licensed users logged in this month."""
    if len(users_df) == 0:
        return 0
    return round(users_df["logged_in_this_month"].apply(lambda x: str(x).upper() in ("TRUE","1","YES")).mean()*100, 1)

def m10_engagement_rate(users_df):
    """% licensed users with at least one manual record this month."""
    if len(users_df) == 0:
        return 0
    return round(users_df["manually_engaged_this_month"].apply(lambda x: str(x).upper() in ("TRUE","1","YES")).mean()*100, 1)


# ─── Status badge helper ───────────────────────────────────────────────
def status(val, green, amber, higher_is_better=True):
    if higher_is_better:
        if val >= green:   return f'<span class="status-green">▲ On track</span>'
        elif val >= amber: return f'<span class="status-amber">● Watch</span>'
        else:              return f'<span class="status-red">▼ At risk</span>'
    else:
        if val <= green:   return f'<span class="status-green">▲ On track</span>'
        elif val <= amber: return f'<span class="status-amber">● Watch</span>'
        else:              return f'<span class="status-red">▼ At risk</span>'

def card(label, value, sub="", status_html="", note=""):
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-sub">{sub} &nbsp; {status_html}</div>
      <div class="data-note">{note}</div>
    </div>""", unsafe_allow_html=True)


# ─── Sidebar — file uploads ────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.shields.io/badge/Ascend-CRM%20Scorecard-1F3864?style=flat-square", width=200)
    st.markdown("### Upload CRM Exports")
    st.caption("All columns must match the spec below. Leave empty to use demo data.")

    up_pipeline = st.file_uploader("pipeline_summary.csv", type="csv", key="pipeline")
    up_opps   = st.file_uploader("opportunities.csv",  type="csv", key="opps")
    up_stages = st.file_uploader("stage_history.csv",  type="csv", key="stages")
    up_refs   = st.file_uploader("referrals.csv",      type="csv", key="refs")
    up_tasks  = st.file_uploader("tasks.csv",          type="csv", key="tasks")
    up_acts   = st.file_uploader("activities.csv",     type="csv", key="acts")
    up_users  = st.file_uploader("users.csv",          type="csv", key="users")

    st.divider()
    st.markdown("**Firm filter**")
    firm_filter = st.multiselect("Show firms", options=[], default=[], key="firm_sel",
                                 placeholder="All firms (select to filter)")

    st.divider()
    with st.expander("📋 CSV column specs"):
        st.markdown("""
**pipeline_summary.csv**
`firm_name, source, intake_pending, opportunity_count, service_line_count, closed_won`

**opportunities.csv**
`opportunity_id, prospect_id, opportunity_type, date_created, actual_completion_date, outcome, firm_id`

**stage_history.csv**
`opportunity_id, stage_name, stage_start_date, stage_end_date, firm_id`

**referrals.csv**
`referral_id, created_date, linked_opportunity_id, linked_opportunity_date, outcome, firm_id`

**tasks.csv**
`task_id, opportunity_id, status, due_date, completion_date, created_by, firm_id`

**activities.csv**
`activity_id, opportunity_id, activity_type, created_by, created_date, firm_id`

**users.csv**
`user_id, firm_id, role, logged_in_this_month, manually_engaged_this_month`

For `created_by`: use `user` or `system`.
For boolean columns: `TRUE`/`FALSE` or `1`/`0`.
        """)


# ─── Load data ────────────────────────────────────────────────────────
# Load pipeline: use upload if provided, otherwise fall back to bundled CSV in repo
if up_pipeline:
    pipeline_df = load_csv(up_pipeline, "pipeline_summary")
else:
    try:
        pipeline_df = pd.read_csv("pipeline_summary.csv")
        pipeline_df.columns = [c.strip().lower().replace(" ", "_") for c in pipeline_df.columns]
    except Exception:
        pipeline_df = None

demo_mode = not any([up_opps, up_stages, up_refs, up_tasks, up_acts, up_users])

if demo_mode:
    opps_df, stages_df, refs_df, tasks_df, acts_df, users_df = generate_demo_data()
else:
    date_cols = {
        "opportunities": ["date_created","actual_completion_date"],
        "stage_history": ["stage_start_date","stage_end_date"],
        "referrals":     ["created_date","linked_opportunity_date"],
        "tasks":         ["due_date","completion_date"],
        "activities":    ["created_date"],
    }
    opps_df   = parse_dates(load_csv(up_opps,   "opportunities") or pd.DataFrame(), date_cols["opportunities"])
    stages_df = parse_dates(load_csv(up_stages, "stage_history") or pd.DataFrame(), date_cols["stage_history"])
    refs_df   = parse_dates(load_csv(up_refs,   "referrals")     or pd.DataFrame(), date_cols["referrals"])
    tasks_df  = parse_dates(load_csv(up_tasks,  "tasks")         or pd.DataFrame(), date_cols["tasks"])
    acts_df   = parse_dates(load_csv(up_acts,   "activities")    or pd.DataFrame(), date_cols["activities"])
    users_df  = load_csv(up_users, "users") or pd.DataFrame()

# Update firm filter options
if "firm_id" in opps_df.columns:
    all_firms = sorted(opps_df["firm_id"].unique().tolist())
    with st.sidebar:
        firm_filter = st.multiselect("Show firms", options=all_firms,
                                     default=all_firms, key="firm_sel2")
    if firm_filter:
        opps_df   = opps_df[opps_df["firm_id"].isin(firm_filter)]
        stages_df = stages_df[stages_df["firm_id"].isin(firm_filter)] if "firm_id" in stages_df.columns else stages_df
        refs_df   = refs_df[refs_df["firm_id"].isin(firm_filter)]     if "firm_id" in refs_df.columns   else refs_df
        tasks_df  = tasks_df[tasks_df["firm_id"].isin(firm_filter)]   if "firm_id" in tasks_df.columns  else tasks_df
        acts_df   = acts_df[acts_df["firm_id"].isin(firm_filter)]     if "firm_id" in acts_df.columns   else acts_df
        users_df  = users_df[users_df["firm_id"].isin(firm_filter)]   if "firm_id" in users_df.columns  else users_df


# ─── Header ───────────────────────────────────────────────────────────
st.markdown("## 📊 CRM Scorecard")
st.caption(f"Ascend Together | Net-new metrics not tracked in existing reports | As of {today.strftime('%B %d, %Y')}")

st.divider()
tab1, tab2 = st.tabs(["Overview", "Coming Soon"])

# ─── Tab 1: Overview (real data) ──────────────────────────────────────
with tab1:
    if pipeline_df is not None and not pipeline_df.empty:
        st.markdown('<div class="section-head">Executive Summary</div>', unsafe_allow_html=True)

        # Segment rows — normalize intake_pending to string for safe comparison
        df = pipeline_df.copy()
        if "intake_pending" not in df.columns:
            df["intake_pending"] = "null"
        df["intake_pending"] = df["intake_pending"].astype(str).str.strip().str.lower()
        df["source"] = df["source"].astype(str).str.strip().str.lower()
        # Accept both naming conventions: ui/manual and email/ai_email
        ui_vals    = ["ui", "manual"]
        email_vals = ["email", "ai_email"]
        manual   = df[df["source"].isin(ui_vals)]
        ai_appr  = df[(df["source"].isin(email_vals)) & (df["intake_pending"] == "false")]
        ai_pend  = df[(df["source"].isin(email_vals)) & (df["intake_pending"] == "true")]
        approved = pd.concat([manual, ai_appr])

        opps_appr  = int(approved["opportunity_count"].sum())
        opps_pend  = int(ai_pend["opportunity_count"].sum())
        sl_appr    = int(approved["service_line_count"].sum())
        sl_pend    = int(ai_pend["service_line_count"].sum())
        total_won  = int(approved["closed_won"].sum())
        won_rate   = round(total_won / opps_appr * 100, 1) if opps_appr else 0

        st.caption("Close Rate and Closed Won are calculated on **approved opportunities only** "
                   "(Manual + AI Email reviewed). AI Email pending review is shown separately.")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            card("Opps — Approved", f"{opps_appr:,}",
                 sub=f"+ {opps_pend:,} pending review",
                 note="Manual entries + AI Email approved by a user.")
        with c2:
            card("Service Lines — Approved", f"{sl_appr:,}",
                 sub=f"+ {sl_pend:,} pending review",
                 note="SLs linked to approved opportunities.")
        with c3:
            card("Closed Won", f"{total_won:,}",
                 sub="approved opps only",
                 note="Opportunities with a Closed Won outcome.")
        with c4:
            card("Close Rate", f"{won_rate}%",
                 sub="Closed Won / approved opps",
                 note="AI pending excluded — not yet in the real pipeline.")
        with c5:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: #f59e0b;">
              <div class="metric-label">Email Opps — Pending Review</div>
              <div class="metric-value" style="color:#b45309;">{opps_pend:,}</div>
              <div class="metric-sub">awaiting user approval</div>
              <div class="data-note">Not counted in any rate metrics until approved.</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("**Breakdown by firm**")
        def firm_agg(seg, col_prefix, value_col):
            return seg.groupby("firm_name")[value_col].sum().rename(col_prefix)

        bd = pd.DataFrame({"firm_name": df["firm_name"].unique()}).set_index("firm_name")
        bd["Opps Approved"]    = firm_agg(approved, "Opps Approved",    "opportunity_count")
        bd["Opps Pending"]     = firm_agg(ai_pend,  "Opps Pending",     "opportunity_count")
        bd["SL Approved"]      = firm_agg(approved, "SL Approved",      "service_line_count")
        bd["SL Pending"]       = firm_agg(ai_pend,  "SL Pending",       "service_line_count")
        bd["Closed Won"]       = firm_agg(approved, "Closed Won",       "closed_won")
        bd = bd.fillna(0).astype(int)
        bd["Close Rate %"] = (bd["Closed Won"] / bd["Opps Approved"].apply(lambda x: x if x > 0 else float("nan")) * 100).fillna(0).round(1)
        bd.index.name = "Firm"
        st.dataframe(bd, use_container_width=True)

        st.markdown("**Intake breakdown by firm** — Manual / AI Approved / AI Pending")
        chart_rows = []
        for _, row in manual.iterrows():
            chart_rows.append({"Firm": row["firm_name"], "Category": "UI Entry", "Opportunities": row["opportunity_count"]})
        for _, row in ai_appr.iterrows():
            chart_rows.append({"Firm": row["firm_name"], "Category": "Email — Approved", "Opportunities": row["opportunity_count"]})
        for _, row in ai_pend.iterrows():
            chart_rows.append({"Firm": row["firm_name"], "Category": "Email — Pending", "Opportunities": row["opportunity_count"]})
        if chart_rows:
            chart_grp = pd.DataFrame(chart_rows).groupby(["Firm", "Category"], as_index=False)[["Opportunities"]].sum()
        else:
            chart_grp = pd.DataFrame(columns=["Firm", "Category", "Opportunities"])

        color_map = {
            "UI Entry":             "#70AD47",
            "Email — Approved":    "#2E75B6",
            "Email — Pending":     "#F59E0B",
        }
        ch1, ch2 = st.columns([2, 1])
        with ch1:
            fig_bar = px.bar(
                chart_grp, x="Firm", y="Opportunities", color="Category",
                barmode="group",
                color_discrete_map=color_map,
                height=340,
            )
            fig_bar.update_layout(margin=dict(t=20, b=20), legend_title_text="")
            st.plotly_chart(fig_bar, use_container_width=True)

        with ch2:
            total_grp = chart_grp.groupby("Category")["Opportunities"].sum().reset_index()
            fig_pie = px.pie(
                total_grp, values="Opportunities", names="Category",
                color="Category",
                color_discrete_map=color_map,
                height=340,
            )
            fig_pie.update_traces(textinfo="percent+label")
            fig_pie.update_layout(margin=dict(t=20, b=20), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

    else:
        st.info("Upload **pipeline_summary.csv** in the sidebar to see the Executive Summary.")


# --- Tab 2: Coming Soon ---
with tab2:
    st.markdown('<div class="section-head">Metrics in Development</div>', unsafe_allow_html=True)
    st.caption("These metrics will be added as CRM data exports become available.")

    coming_soon = [
        ("Deal Velocity", [
            ("M1", "Average Stage Dwell Time", "How long opportunities sit in each stage before moving forward."),
            ("M2", "Referral Response Time", "Days from referral created to first opportunity logged."),
        ]),
        ("Pipeline Health", [
            ("M3", "Stage Conversion Rate", "% of opportunities that reached each stage."),
        ]),
        ("Referral Performance", [
            ("M4", "Referral-to-Won Conversion", "% of referrals that resulted in a closed won opportunity."),
        ]),
        ("Operational Efficiency", [
            ("M5", "Task Completion Rate", "% of user-created tasks completed on time."),
            ("M6", "Overdue Task Rate", "% of open tasks past their due date."),
            ("M7", "Opportunities Logged YTD", "New opportunities created year-to-date vs prior year."),
            ("M8", "User-Initiated Activities per Opp", "Avg calls, notes, meetings per closed opportunity."),
        ]),
        ("Adoption", [
            ("M9",  "Login Rate", "% of licensed users who logged in this month."),
            ("M10", "Manual Engagement Rate", "% of licensed users who created at least one record this month."),
        ]),
    ]

    for category, metrics in coming_soon:
        st.markdown(f"**{category}**")
        for code, name, desc in metrics:
            st.markdown(f"- **{code} -- {name}:** {desc}")
        st.write("")


# --- Footer ---
st.divider()
st.caption("Ascend Together | CRM Program | As of " + today.strftime('%B %d, %Y'))
