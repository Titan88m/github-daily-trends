import os, json, time, datetime, pathlib, re, requests
API="https://api.github.com"
TOKEN=os.getenv("GITHUB_TOKEN","")
H={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
if TOKEN:H["Authorization"]="Bearer "+TOKEN
NOW=datetime.datetime.now(datetime.timezone.utc)
TODAY=NOW.date().isoformat()
DATA=pathlib.Path("data");DATA.mkdir(exist_ok=True)
HISTORY=DATA/"history.json"
def get(url,params=None):
    r=requests.get(url,headers=H,params=params,timeout=30)
    if r.status_code==403 and "rate limit" in r.text.lower(): raise RuntimeError("GitHub API rate limit reached")
    r.raise_for_status();return r.json()
def load(path,default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except:return default
def search(query):
    out=[]
    for page in range(1,6):
        d=get(API+"/search/repositories",{"q":query,"sort":"updated","order":"desc","per_page":100,"page":page})
        out.extend(d.get("items",[]))
        if len(d.get("items",[]))<100:break
        time.sleep(.15)
    return out
def is_persian(repo):
    text=" ".join([repo.get("description") or "",repo.get("full_name") or ""," ".join(repo.get("topics") or [])])
    if re.search(r"[\u0600-\u06ff]",text):return True
    try:
        branch=repo.get("default_branch") or "main"
        x=requests.get(f'{API}/repos/{repo["full_name"]}/readme',headers={**H,"Accept":"application/vnd.github.raw+json"},params={"ref":branch},timeout=12)
        if x.ok and re.search(r"[\u0600-\u06ff]",x.text[:50000]):return True
    except:pass
    return False
def compact(r,old,scope):
    full=r["full_name"];prev=old.get(full,{})
    return {"id":r["id"],"full_name":full,"html_url":r["html_url"],"description":r.get("description") or "",
      "description_fa":r.get("description") or "مخزن متن‌باز؛ برای جزئیات بیشتر README را ببینید.",
      "language":r.get("language"),"topics":r.get("topics") or [],"stars":r.get("stargazers_count",0),
      "growth":max(0,r.get("stargazers_count",0)-prev.get("stars",r.get("stargazers_count",0))),
      "updated_at":r.get("updated_at"),"repeated":full in old}
def main():
    previous=load(DATA/"latest.json",{})
    oldmap=previous.get("repositories",{})
    since=(NOW.date()-datetime.timedelta(days=30)).isoformat()
    candidates=search(f"stars:>5 pushed:>={since}")
    unique={r["full_name"]:r for r in candidates}
    # Persian-language projects are found independently, then validated against repository metadata/README.
    persian_candidates=search(f"stars:>1 pushed:>={since} language:Python")
    for r in persian_candidates:unique.setdefault(r["full_name"],r)
    persian=[r for r in unique.values() if is_persian(r)]
    global_rows=[r for r in unique.values() if r not in persian]
    # Save current counters for the next scheduled run.
    repos={r["full_name"]:{"stars":r.get("stargazers_count",0),"seen":TODAY} for r in unique.values()}
    snapshot={"date":TODAY,"tracked_count":len(unique),"new_count":sum(1 for k in repos if k not in oldmap),"repositories":repos}
    hist=load(HISTORY,[])
    hist=[x for x in hist if x.get("date")!=TODAY]+[snapshot]
    hist=sorted(hist,key=lambda x:x["date"])[-400:]
    HISTORY.write_text(json.dumps(hist,ensure_ascii=False,indent=2),encoding="utf-8")
    def rank(rows,days):
        start=NOW-datetime.timedelta(days=days)
        # Compare against the closest available historical snapshot at/before the requested horizon.
        target=(NOW.date()-datetime.timedelta(days=days)).isoformat()
        past=next((x for x in reversed(hist[:-1]) if x["date"]<=target),None)
        result=[]
        for r in rows:
            oldstars=(past or {}).get("repositories",{}).get(r["full_name"],{}).get("stars")
            delta=max(0,r.get("stargazers_count",0)-(oldstars if oldstars is not None else r.get("stargazers_count",0)))
            if days==1 and oldstars is None:delta=0
            item=compact(r,oldmap,"")
            item["growth"]=delta
            item["history_ready"]=past is not None
            result.append(item)
        return sorted(result,key=lambda x:(x["growth"],x["stars"]),reverse=True)[:20]
    rankings={}
    for name,rows in (("global",global_rows),("persian",persian)):
        rankings[name]={"24h":rank(rows,1),"7d":rank(rows,7),"30d":rank(rows,30)}
    output={"generated_at":NOW.isoformat(),"tracked_count":len(unique),"new_count":snapshot["new_count"],
      "history":hist,"rankings":rankings,"repositories":repos,
      "coverage_note":"Persian classification is heuristic (Persian script in metadata/README); ranking growth requires historical snapshots."}
    (DATA/"latest.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":main()
