"""Combine immutable existing layer captures and small fresh captures one layer at a time."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import pickle
import time


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);a=p.parse_args();start=time.time()
    r=a.root;old=a.reference
    questions=json.loads((old/'questions.json').read_text())['items'];fresh=json.loads((r/'fresh.json').read_text())['items']
    assert len(questions)==812 and len(fresh)==64
    new_meta=json.loads((r/'fresh_traj/meta.json').read_text());old_meta=json.loads((old/'traj/meta.json').read_text())
    assert new_meta['meta']['complete'] and old_meta['meta']['complete']
    for k in ('n_sys','prompt_hash','layers','schema'):assert new_meta['meta'][k]==old_meta['meta'][k],k
    both=questions+fresh;traj=r/'traj';traj.mkdir(exist_ok=True)
    identities={str(x):sha(x) for x in (old/'questions.json',r/'fresh.json',old/'traj/meta.json',r/'fresh_traj/meta.json')}
    state_path=traj/'merge_progress.json';done=[]
    if state_path.exists():
        state=json.loads(state_path.read_text());assert state['identities']==identities;done=state['layers']
    import numpy as np
    layers=old_meta['meta']['layers']
    for layer in layers:
        if layer in done:continue
        with (old/f'traj/layer_{layer:03d}.pkl').open('rb') as f:left=pickle.load(f)
        with (r/f'fresh_traj/layer_{layer:03d}.pkl').open('rb') as f:right=pickle.load(f)
        assert len(left['traj'])==812 and len(right['traj'])==64
        assert all(np.array_equal(left[k],right[k]) for k in ('k_sys','v_sys'))
        for i,row in enumerate(right['traj']):
            assert row['item']==i and row['q']==fresh[i]['q']
            row['item']=812+i
        left['traj'].extend(right['traj'])
        path=traj/f'layer_{layer:03d}.pkl';part=path.with_suffix('.partial')
        with part.open('wb') as f:pickle.dump(left,f,protocol=pickle.HIGHEST_PROTOCOL)
        part.replace(path);del left,right
        done.append(layer);part=state_path.with_suffix('.partial')
        part.write_text(json.dumps({'identities':identities,'layers':done},indent=2)+'\n');part.replace(state_path)
        elapsed=time.time()-start;rate=len(done)/max(elapsed,.001)
        print(f'{datetime.now(timezone.utc).isoformat()} merge elapsed={elapsed:.1f}s completed={len(done)}/{len(layers)} rate={rate:.3f}/s ETA={(len(layers)-len(done))/rate:.1f}s',flush=True)
    from sys import path as syspath
    syspath.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    import exl3
    metadata=dict(old_meta['meta'],source=str(r/'questions.json'),n_items=876,complete=True,
                  items_hash=exl3.prompt_hash(json.dumps(both,sort_keys=True)),
                  merged_existing=812,fresh=64,position_plan_sha256=sha(r/'positions.json'),elapsed_s=time.time()-start)
    index=old_meta['index']+[dict(row,item=812+i) for i,row in enumerate(new_meta['index'])]
    (r/'questions.json').write_text(json.dumps({'items':both},indent=2)+'\n')
    part=traj/'meta.partial';part.write_text(json.dumps({'meta':metadata,'index':index},indent=2)+'\n');part.replace(traj/'meta.json')
    plans={'control':{'groups':[{'indices':list(range(780)),'count':48},{'indices':list(range(780,812)),'count':24}]},
           'candidate':{'groups':[{'indices':list(range(780)),'count':48},{'indices':list(range(780,812)),'count':8},{'indices':list(range(812,876)),'count':16}]}}
    for label,plan in plans.items():
        text=json.dumps(plan,indent=2)+'\n';path=r/f'{label}_sampling.json'
        if path.exists():assert path.read_text()==text
        else:path.write_text(text)
    (r/'merge_result.json').write_text(json.dumps({'complete':True,'elapsed_s':time.time()-start,'old_rows':812,'fresh_rows':64,'total_rows':876,'teacher_kv_equal_all_layers':True},indent=2)+'\n')
    print(f'DONE merge_duration={time.time()-start:.3f}s artifact={traj}',flush=True)


if __name__=='__main__':main()
