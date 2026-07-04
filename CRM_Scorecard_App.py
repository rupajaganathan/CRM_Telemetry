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

if demo_mode:
    st.markdown('<div class="demo-banner">⚠ <strong>Demo mode</strong> — showing sample data. Upload your CRM CSV exports in the sidebar to see real numbers.</div>', unsafe_allow_html=True)

st.divider()


# ─── M1 + M2: Deal Velocity ───────────────────────────────────────────
st.markdown('<div class="section-head">Deal Velocity</div>', unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])

with col1:
    dwell = m1_stage_dwell(stages_df) if len(stages_df) else pd.Series(dtype=float)
    st.markdown("**M1 — Average Stage Dwell Time** (days)")
    if not dwell.empty:
        bottleneck = dwell.idxmax()
        st.dataframe(
            dwell.reset_index().rename(columns={"stage_name": "Stage", "days": "Avg Days"}),
            use_container_width=True, hide_index=True
        )
        st.caption(f"Longest stage: **{bottleneck}** ({dwell.max()} days avg)")
    else:
        st.info("No stage history data available.")

with col2:
    if len(refs_df):
        avg_days, gap_pct = m2_referral_response(refs_df)
        card(
            "M2 — Referral Response Time",
            f"{avg_days} days",
            sub=f"{gap_pct}% of referrals had no Opportunity within 90 days",
            status_html=status(avg_days, 14, 21, higher_is_better=False),
            note="Avg days: Referral created → first Opportunity. Excludes referrals with no linked Opportunity."
        )
    else:
        st.info("No referral data available.")


# ─── M3: Pipeline Health ──────────────────────────────────────────────
st.markdown('<div class="section-head">Pipeline Health</div>', unsafe_allow_html=True)

conv = m3_stage_conversion(stages_df, opps_df) if (len(stages_df) and len(opps_df)) else pd.Series(dtype=float)
st.markdown("**M3 — Stage Conversion Rate** (% of all Opportunities that reached each stage)")
if not conv.empty:
    import streamlit as _st
    conv_df = conv.reset_index().rename(columns={"index": "Stage", 0: "% Reached"})
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.bar_chart(conv, use_container_width=True, color="#2E75B6", height=220)
    with col_b:
        st.dataframe(conv_df, use_container_width=True, hide_index=True)
else:
    st.info("No stage or opportunity data available.")


# ─── M4: Referral Performance ─────────────────────────────────────────
st.markdown('<div class="section-head">Referral Performance</div>', unsafe_allow_html=True)

if len(refs_df):
    won_pct, opp_pct = m4_referral_conversion(refs_df)
    col1, col2 = st.columns(2)
    with col1:
        card("M4 — Referral-to-Won Conversion Rate", f"{won_pct}%",
             sub=f"{opp_pct}% of referrals became an Opportunity",
             status_html=status(won_pct, 40, 25),
             note="Won / total Referrals. Distinct from win rate by source (which only counts deals already in pipeline).")
    with col2:
        total_refs = len(refs_df)
        no_opp = refs_df["linked_opportunity_id"].isna().sum()
        card("Referral Gap", f"{no_opp} of {total_refs}",
             sub="referrals with no Opportunity logged",
             note="These referrals never entered the pipeline.")
else:
    st.info("No referral data available.")


# ─── M5–M8: Operational Efficiency ───────────────────────────────────
st.markdown('<div class="section-head">Operational Efficiency</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if len(tasks_df):
        tc = m5_task_completion(tasks_df)
        card("M5 — Task Completion Rate", f"{tc}%",
             status_html=status(tc, 70, 50),
             note="User-created tasks only. Excludes system auto-tasks.")
    else:
        st.info("No task data.")

with col2:
    if len(tasks_df):
        od = m6_overdue_tasks(tasks_df)
        card("M6 — Overdue Task Rate", f"{od}%",
             sub="of open tasks are past due",
             status_html=status(od, 15, 30, higher_is_better=False),
             note="Open tasks with DueDate < today.")
    else:
        st.info("No task data.")

with col3:
    if len(opps_df):
        ytd = m7_opps_ytd(opps_df)
        card("M7 — Opportunities Logged YTD", f"{ytd:,}",
             note=f"Opportunities created in {today.year}.")
    else:
        st.info("No opportunity data.")

with col4:
    if len(acts_df) and len(opps_df):
        apo = m8_activities_per_opp(acts_df, opps_df)
        card("M8 — User-Initiated Activities / Opp", f"{apo}",
             status_html=status(apo, 4, 2),
             note="Calls, Notes, Meetings per closed Opp. Excludes Fireflies & auto-email.")
    else:
        st.info("No activity data.")


# ─── M9–M10: Adoption ─────────────────────────────────────────────────
st.markdown('<div class="section-head">Adoption</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 2])

if len(users_df):
    login_r = m9_login_rate(users_df)
    eng_r   = m10_engagement_rate(users_df)
    gap     = round(login_r - eng_r, 1)

    with col1:
        card("M9 — Login Rate", f"{login_r}%",
             sub=f"of {len(users_df)} licensed users logged in this month",
             status_html=status(login_r, 70, 50),
             note="Access signal.")

    with col2:
        card("M10 — Manual Engagement Rate", f"{eng_r}%",
             sub=f"created at least one user-initiated record",
             status_html=status(eng_r, 55, 35),
             note="Genuine use signal. Excludes system-generated records.")

    with col3:
        st.markdown("**Adoption gap by firm**")
        if "firm_id" in users_df.columns:
            def firm_stats(df):
                out = []
                for firm, grp in df.groupby("firm_id"):
                    lr = grp["logged_in_this_month"].apply(lambda x: str(x).upper() in ("TRUE","1","YES")).mean() * 100
                    er = grp["manually_engaged_this_month"].apply(lambda x: str(x).upper() in ("TRUE","1","YES")).mean() * 100
                    out.append({"Firm": firm, "Login %": round(lr,1), "Engaged %": round(er,1),
                                "Gap": round(lr-er,1), "Users": len(grp)})
                return pd.DataFrame(out).sort_values("Gap", ascending=False)
            firm_df = firm_stats(users_df)
            st.dataframe(firm_df, use_container_width=True, hide_index=True)
            st.caption("Gap = Login Rate − Engagement Rate. High gap = users accessing but not using.")
        else:
            st.metric("Login vs Engaged gap", f"{gap}pp",
                      help="Users logging in but not creating records.")
else:
    st.info("No user data available.")


# ─── Footer ───────────────────────────────────────────────────────────
st.divider()
st.caption("Ascend Together | CRM Program | These metrics are not tracked in existing reports or dashboards. "
           "For questions contact the CRM Program team.")
