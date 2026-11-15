"""Duckweed chamber dashboard (starter). Run with:  streamlit run app.py
Reads the database only. The logger and camera_job write to it.
Everything seeded by simulate.py is MADE-UP demo data."""
import os

import pandas as pd
import streamlit as st

import db
import simulate

MAX_PUMP_SECONDS = 10      # also enforced in logger.py
LOW_WATER_MM = 25          # from Meeting 7 minutes, to confirm with Kai

st.set_page_config(page_title="Duckweed Lab", page_icon="🌱", layout="wide")

st.markdown("""
<style>
.stButton > button { font-size: 1.3rem; padding: 0.7rem 1.4rem; border-radius: 12px; }
.card { border: 2px solid #cfd8dc; border-radius: 14px; padding: 14px 18px; margin-bottom: 10px; }
.card h3 { margin: 0 0 4px 0; }
.big { font-size: 3rem; font-weight: 700; line-height: 1.1; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_conn():
    conn = db.connect()
    simulate.seed(conn)
    return conn


def health(df):
    """PLACEHOLDER rules. The real colour metric is still to be agreed with Jenn and Emmanuel."""
    last = df.iloc[-1]
    if pd.notna(last["greenness"]) and last["greenness"] < 0.40:
        return "🟡", "Needs help", "The plants look pale. Ask your teacher to check them."
    recent = df[df["hours"] >= last["hours"] - 24]
    if len(recent) > 1 and recent["coverage_pct"].iloc[-1] <= recent["coverage_pct"].iloc[0]:
        return "🟠", "Needs a check", "No new growth in the last day."
    return "🟢", "Growing well", "The duckweed is spreading across the dish."


conn = get_conn()
exps = db.experiments(conn)
live = next((e for e in exps if not e["is_reference"]), exps[0])

st.sidebar.title("🌱 Duckweed Lab")
mode = st.sidebar.radio("Who is using this?", ["Student", "Teacher"])
st.sidebar.caption("Demo data: the numbers and photos here are made up, not real results.")


# ---------------------------------------------------------------- student
EXPLAIN = {
    "White": "White light has every colour in it, so the plants get a bit of everything.",
    "Blue": "Blue light is used by plants to grow leaves, but on its own it may not be enough.",
    "Red": "Red light gives plants lots of energy for growing, which can make them spread quickly.",
}


def reference_results():
    """Final coverage (%) of each example run, plus the winner. Demo data for now."""
    frames, final = [], {}
    for e in exps:
        if e["is_reference"]:
            d = db.readings_df(conn, e["id"])
            if not d.empty:
                frames.append(d.groupby("day")["coverage_pct"].mean().rename(e["name"]))
                final[e["light"].capitalize()] = float(d["coverage_pct"].iloc[-1])
    winner = max(final, key=final.get) if final else None
    return frames, final, winner


def look_tab(df):
    last = df.iloc[-1]
    left, right = st.columns([1, 1])
    with left:
        if last["photo_path"] and os.path.exists(last["photo_path"]):
            st.image(last["photo_path"], caption="Latest photo of our dish")
    with right:
        cov = float(last["coverage_pct"]) if pd.notna(last["coverage_pct"]) else 0.0
        st.markdown(f"<div class='card'><h3>🟩 How much of the dish is green?</h3>"
                    f"<div class='big'>{cov:.0f}%</div></div>", unsafe_allow_html=True)
        st.progress(min(int(cov), 100) / 100)
        icon, title, msg = health(df)
        st.markdown(f"<div class='card'><h3>{icon} {title}</h3>{msg}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        wl = last["water_level_mm"]
        if pd.notna(wl):
            water_icon, water_txt = ("💧", "Water is fine") if wl >= LOW_WATER_MM else ("🚨", "Water is low!")
            c1.markdown(f"<div class='card'><h3>{water_icon} Water</h3>{water_txt}</div>", unsafe_allow_html=True)
        if pd.notna(last["temperature_c"]):
            c2.markdown(f"<div class='card'><h3>🌡️ Temperature</h3>{last['temperature_c']:.1f} °C</div>",
                        unsafe_allow_html=True)
    st.subheader("Growth so far")
    st.line_chart(df.set_index("day")["coverage_pct"], y_label="% green", x_label="Days")
    st.caption("Tip: look at the line. Is it going up quickly, slowly, or has it stopped?")


def experiment_tab():
    """Predict, watch, explain. Each step is saved before the next one shows."""
    step = st.session_state.get("step", 1)
    frames, final, winner = reference_results()
    st.progress(step / 3, text=f"Step {step} of 3")

    if step == 1:
        st.header("1. 🔮 Predict")
        st.write("A scientist makes a guess *before* the test. That is called a **prediction**.")
        st.write("Our chamber can only grow one thing at a time, and duckweed takes days to grow. "
                 "So we ran the test already. Before you see the answer: **which colour of light "
                 "will make duckweed spread the most?**")
        st.text_input("Pick a nickname (not your real name)", key="nick_widget", max_chars=20)
        pick = st.radio("My prediction", ["White", "Blue", "Red"], horizontal=True, key="pick_widget")
        st.text_input("Why do you think so? (one sentence)", key="why_widget", max_chars=140)
        if st.button("Lock in my prediction 🔒"):
            st.session_state["nick"] = st.session_state.get("nick_widget") or "Anonymous"
            st.session_state["guess"] = pick     # saved under our own keys: widget state is lost when not shown
            st.session_state["why"] = st.session_state.get("why_widget", "")
            st.session_state["step"] = 2
            st.rerun()

    elif step == 2:
        st.header("2. 👀 Watch")
        st.write(f"You predicted **{st.session_state['guess']}**. Here is what really happened "
                 "when we grew duckweed under each light for 8 days.")
        if frames:
            st.line_chart(pd.concat(frames, axis=1), y_label="% green", x_label="Days")
        st.write("**Look for:** which line ends highest? Which line starts slowly?")
        st.caption("Example runs: made-up demo data for now.")
        if st.button("I've seen enough ➡️"):
            st.session_state["step"] = 3
            st.rerun()

    else:
        st.header("3. 💬 Explain")
        guess = st.session_state["guess"]
        right = winner == guess
        st.write(f"You predicted **{guess}**. The fastest grower was **{winner}** "
                 f"({final.get(winner, 0):.0f}% green).")
        if right:
            st.success("You were right! 🎉 Good scientists check their ideas against the data.")
        else:
            st.info("Not this time, and that is great science. A surprise means you learned something.")
        st.write(f"**A possible reason:** {EXPLAIN.get(winner, '')}")
        reflection = st.text_area("In your own words: what did the lines show, and why do you think it happened?",
                                  key="reflect_widget", max_chars=300)
        c1, c2 = st.columns(2)
        if c1.button("Save my answer 💾"):
            db.add_prediction(conn, st.session_state["nick"], guess, st.session_state.get("why", ""),
                              reflection, right)
            st.success("Saved! Your teacher can see it.")
        if c2.button("Try again 🔁"):
            st.session_state["step"] = 1
            st.rerun()


def help_tab():
    st.header("📖 What do the words mean?")
    with st.expander("🟩 What is '% green'?"):
        st.write("The camera takes a photo of the dish. The computer counts how much of the dish is "
                 "covered in green plants. 50% means half the dish is covered.")
    with st.expander("🌡️ Why does temperature matter?"):
        st.write("Plants grow best when it is not too hot and not too cold. Ours likes it a bit warm.")
    with st.expander("💧 Why do we watch the water?"):
        st.write("Duckweed floats on water. If the water gets too low, it dries out. "
                 "The pump tops it up, and your teacher controls that.")
    with st.expander("💡 Why does light colour matter?"):
        st.write("Plants use light as food. Different colours of light give them different amounts of energy.")
    with st.expander("🔮 What is a prediction?"):
        st.write("A guess you make before a test, so you can check afterwards whether you were right.")
    st.caption("Colours always come with a word or picture too, so everyone can read the screen.")


def student_view():
    df = db.readings_df(conn, live["id"])
    st.title("🌱 Our duckweed")
    if df.empty:
        st.info("No readings yet. Check back soon!")
        return
    t1, t2, t3 = st.tabs(["👀 Look", "🔮 Experiment", "📖 Help"])
    with t1:
        look_tab(df)
    with t2:
        experiment_tab()
    with t3:
        help_tab()


# ---------------------------------------------------------------- teacher
def teacher_view():
    st.title("Teacher view")
    tab_live, tab_cmp, tab_ctl, tab_cls, tab_exp = st.tabs(
        ["Live data", "Compare experiments", "Controls", "Class predictions", "Export"])

    with tab_live:
        df = db.readings_df(conn, live["id"])
        if df.empty:
            st.info("No readings yet.")
        else:
            st.dataframe(df.drop(columns=["photo_path"]).tail(20), width="stretch")
            st.line_chart(df.set_index("ts")[["temperature_c", "humidity_pct", "water_level_mm"]])

    with tab_cmp:
        names = {e["name"]: e["id"] for e in exps}
        chosen = st.multiselect("Experiments", list(names), default=list(names))
        metric = st.selectbox("Measure", ["coverage_pct", "greenness", "temperature_c", "water_level_mm"])
        frames = []
        for n in chosen:
            d = db.readings_df(conn, names[n])
            if not d.empty:
                frames.append(d.groupby("day")[metric].mean().rename(n))
        if frames:
            st.line_chart(pd.concat(frames, axis=1))

    with tab_ctl:
        st.warning("Commands go to the logger, which sends them to the microcontroller. "
                   f"Pump runs are capped at {MAX_PUMP_SECONDS} s.")
        secs = st.slider("Pump seconds", 1, MAX_PUMP_SECONDS, 3)
        c1, c2, c3 = st.columns(3)
        if c1.button("Run pump"):
            db.queue_command(conn, "pump", "run", secs)
        if c2.button("Fan on/off"):
            db.queue_command(conn, "fan", "toggle")
        if c3.button("Light on/off"):
            db.queue_command(conn, "light", "toggle")
        st.subheader("Recent commands")
        st.dataframe(db.recent_commands(conn), width="stretch")

    with tab_cls:
        p = db.predictions_df(conn)
        if p.empty:
            st.info("No predictions saved yet. Students save them at the end of the Experiment tab.")
        else:
            st.metric("Predictions", len(p), f"{p['was_right'].mean() * 100:.0f}% correct")
            st.bar_chart(p["guess"].value_counts())
            st.dataframe(p.drop(columns=["id"]), width="stretch")

    with tab_exp:
        names = {e["name"]: e["id"] for e in exps}
        n = st.selectbox("Experiment to export", list(names))
        d = db.readings_df(conn, names[n])
        st.download_button("Download CSV", d.to_csv(index=False), file_name=f"{n}.csv", mime="text/csv")


student_view() if mode == "Student" else teacher_view()
