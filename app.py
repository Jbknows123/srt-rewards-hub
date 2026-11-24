import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTT2-mDol0Er7iIehO4P0y2CmEa3fQbuMH-G5_3D1_mPpcLMO46YrOvgvoIn2V--AF-bMdG8INMo3K8/pub?gid=0&single=true&output=csv'
GOAL = 100
START = date(2026,11,23)
END = START + timedelta(days=6)
st.set_page_config(page_title='SRT Rewards Hub', page_icon='🌠', layout='wide')
st.markdown('''<style>
.stApp {background:#100d17;color:#f5f0ff} [data-testid="stMetric"] {background:#21182f;border:1px solid #483263;border-radius:14px;padding:18px} h1,h2,h3 {color:#d5b4ff!important} .stProgress > div > div > div > div {background:#a855f7} .hero {background:linear-gradient(120deg,#25113e,#512184);padding:30px;border-radius:18px;margin-bottom:20px;color:white} .hero h1 {margin:0;color:white!important} .reward {background:#21182f;border:1px solid #63418b;padding:20px;border-radius:14px;margin-bottom:12px;color:white}
</style><div class="hero"><small>SRT MOTORS / EMPLOYEE REWARDS</small><h1>WISH WEEK</h1><p>100 recruits. One team. Three wishes. One wheel spin.</p></div>''',unsafe_allow_html=True)
@st.cache_data(ttl=30)
def load():
    df=pd.read_csv(URL)
    df.columns=df.columns.str.strip().str.lower()
    if not {'date','recruiter','recruits'}.issubset(df.columns):
        raise ValueError('Sheet must contain Date, Recruiter and Recruits headers.')
    df['date']=pd.to_datetime(df['date'],errors='coerce',format='mixed').dt.date
    df['recruiter']=df['recruiter'].fillna('').astype(str).str.strip()
    df['recruits']=pd.to_numeric(df['recruits'],errors='coerce')
    df=df[df['date'].notna() & df['recruiter'].ne('') & df['recruits'].notna() & (df['recruits']>0) & (df['recruits']%1==0)].copy()
    if 'verified by' in df.columns:
        df=df[df['verified by'].fillna('').astype(str).str.strip().ne('')]
    df=df[df['date'].between(START,END)]
    df['recruits']=df['recruits'].astype(int)
    return df

@st.fragment(run_every=30)
def dashboard():
    try:
        df=load()
    except Exception as e:
        st.error(f'Unable to load recruitment data: {e}')
        return
    now=datetime.now(ZoneInfo('America/Los_Angeles'))
    deadline=datetime.combine(END+timedelta(days=1),datetime.min.time(),tzinfo=now.tzinfo)
    remaining=max(0,int((deadline-now).total_seconds()))
    total=int(df['recruits'].sum())
    ranks=df.groupby('recruiter')['recruits'].sum().sort_values(ascending=False)
    st.caption(f'{START:%b %d} – {END:%b %d, %Y} • Pacific time • Refreshes every 30 seconds')
    a,b,c,d=st.columns(4)
    a.metric('Total recruits',f'{total} / {GOAL}')
    b.metric('Remaining',max(0,GOAL-total))
    c.metric('Active recruiters',len(ranks))
    d.metric('Time remaining',f'{remaining//86400}d {remaining%86400//3600}h' if remaining else 'Ended')
    st.progress(min(total/GOAL,1),text=f'{total/GOAL:.0%} of weekly goal')
    if total>=GOAL: st.success('REWARDS UNLOCKED — subject to final verification')
    else: st.info(f'{max(0,GOAL-total)} more recruits to unlock all four rewards.')
    left,right=st.columns(2)
    with left:
        st.subheader('Recruitment leaderboard')
        if ranks.empty: st.caption('No verified recruits logged yet.')
        else:
            table=ranks.rename('Recruits').reset_index().rename(columns={'recruiter':'Recruiter'})
            table.insert(0,'Rank',table['Recruits'].rank(method='min',ascending=False).astype(int))
            st.dataframe(table,hide_index=True,use_container_width=True)
            st.caption('Ties require management review. Final winners are confirmed by SRT.')
    with right:
        st.subheader('Daily recruitment')
        daily=df.groupby('date')['recruits'].sum().reindex([START+timedelta(days=i) for i in range(7)],fill_value=0)
        daily.index=[d.strftime('%a') for d in daily.index]
        st.bar_chart(daily,color='#a855f7')
    st.subheader('Rewards')
    cols=st.columns(4)
    for col,label,prize in zip(cols,['🥇 First place','🥈 Second place','🥉 Third place','🎡 Lucky recruiter'],['One wish','One wish','One wish','One wheel spin']):
        with col:
            st.markdown(f'<div class="reward"><small>{"🔓 UNLOCKED" if total>=GOAL else "🔒 LOCKED"}</small><h3>{label}</h3>{prize}</div>',unsafe_allow_html=True)
    st.caption('No cash alternatives. Wishes require ownership approval. Wheel winner selected outside the top three. Regular recruitment payments are separate.')
    st.caption(f'Last checked: {now:%I:%M:%S %p} PT. Google publishing may introduce a delay.')
    if st.button('Refresh now'):
        load.clear(); st.rerun()
dashboard()
