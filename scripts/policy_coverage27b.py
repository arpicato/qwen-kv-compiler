"""Train-only behavior diversity and CPU audit of captured answer coverage."""
import argparse
import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import pickle
import re
import sys
import time


def training():
    rows=[]
    rules=[
        ('caption','caption','not caption','not caption or not caption.strip()',['',' ','caption'],'reject whitespace-only captions'),
        ('identifier','identifier','not identifier',"not identifier or '-' in identifier",['','id','a-b'],'reject hyphens in identifiers'),
        ('access','access','not access',"access not in ('public', 'private')",['','public','private','root'],'accept only public and private access'),
        ('shards','shards','shards < 0','shards <= 0',[-1,0,1,8],'reject zero shards as well as negative counts'),
        ('hostname','host','not host',"not host or ' ' in host",['','server','a b'],'reject spaces in hostnames'),
        ('label-width','label','not label','not label or len(label) > 18',['','a','a'*18,'a'*19],'reject labels longer than eighteen characters'),
        ('sequence','sequence','sequence < 0','sequence <= 0',[-2,0,1,6],'require sequence numbers to start at one'),
        ('precision','precision','precision < 0','precision < 0 or precision > 6',[-1,0,6,7],'reject display precision above six digits'),
        ('storage','storage','not storage',"storage not in ('disk', 'memory')",['','disk','memory','remote'],'accept only disk and memory storage'),
        ('pathname','path','not path',"not path or path.startswith('/')",['','relative','/absolute'],'reject absolute path strings'),
        ('bucket','bucket','not bucket',"not bucket or bucket.endswith('.')",['','abc','abc.'],'reject bucket names ending with a dot'),
        ('reader-count','readers','readers < 0','readers <= 0',[-1,0,1,3],'require at least one reader'),
        ('locale-length','locale','not locale','not locale or len(locale) > 8',['','fr','a'*8,'a'*9],'reject locale tags longer than eight characters'),
        ('extension-count','extensions','extensions < 0','extensions < 0 or extensions > 10',[-1,0,10,11],'reject more than ten extensions'),
        ('separator','separator','not separator',"separator not in (',', ';')",['',',',';','|'],'accept only comma and semicolon separators'),
        ('version-count','version','version < 0','version <= 0',[-1,0,1,2],'require a positive version count')]
    for i,(name,arg,old,new,values,desc) in enumerate(rules):
        for style in ('validate','normalize'):
            left,right=(('register','restore') if style=='validate' else ('encode','decode'))
            source=f'def {left}({arg}):\n    if {old}:\n        raise ValueError("invalid")\n    return {arg}\n\ndef {right}({arg}):\n    if {old}:\n        raise ValueError("invalid")\n    return {{"data": {arg}}}\n'
            helper=f'def _validated({arg}):\n    if {new}:\n        raise ValueError("invalid")\n    return {arg}\n\n'
            patch=helper+f'def {left}({arg}):\n    return _validated({arg})\n\ndef {right}({arg}):\n    return {{"data": _validated({arg})}}\n'
            wording=('Both functions intentionally implement the same validation rule.' if style=='validate' else 'The two entry points must stay consistent when accepting input.')
            q=f'Please update both functions to {desc}. {wording} Preserve public signatures and valid outputs.\n\n'+source
            rows.append(dict(id=f'coverage-{name}-{style}',q=q,answer='```python\n'+patch+'```',kind='lookup',group='shared',names=[left,right],values=values,argument=arg,new_condition=new))
        if i<8:
            patch=source.replace(f'if {old}:',f'if {new}:',1)
            q=f'Update {left} to {desc}. {right} has a legacy input contract and must stay unchanged, even where the inputs look similar.\n\n'+source
            rows.append(dict(id=f'coverage-{name}-distinct',q=q,answer='```python\n'+patch+'```',kind='lookup',group='distinct',names=[left,right],values=values,argument=arg,new_condition=new))
    ordinary=[('trim_memo','memo','memo.strip()','Trim surrounding whitespace from a transaction memo, without changing money values.'),
        ('display_units','units',"str(units)",'Return the stock quantity as display text. Do not change its numeric meaning.'),
        ('format_region','region','region.upper()','Uppercase the region label on an invoice. Amounts are unaffected.'),
        ('clean_contact','contact','contact.strip()','Remove surrounding whitespace from the receipt contact.'),
        ('queue_size','jobs','len(jobs)','Return the number of queued jobs rather than the list itself.'),
        ('status_label','status','status.lower()','Lowercase the payment status label; this is only display formatting.'),
        ('clean_reference','reference','reference.strip()','Trim the statement reference string; it is not an amount.'),
        ('null_note','note',"'' if note is None else note",'Return an empty note string instead of None, preserving supplied strings.'),
        ('copy_ids','ids','list(ids)','Return a copy of the identifier list rather than the same list object.'),
        ('job_ready','ready','bool(ready)','Normalize a job readiness flag to a boolean.'),
        ('count_rows','rows','len(rows)','Return the number of data rows.'),
        ('trim_report','report','report.rstrip()','Strip trailing whitespace from a report label.'),
        ('receipt_name','name','name.upper()','Uppercase the printed receipt name.'),
        ('first_item','items','items[0] if items else None','Return the first inventory entry or None for an empty list.'),
        ('invoice_title','title','title.strip()','Trim the invoice title, not its amount.'),
        ('batch_label','label','label.lower()','Lowercase the batch label, without affecting batch contents.')]
    for name,arg,expr,desc in ordinary:
        code=f'def {name}({arg}):\n    return {arg}\n'
        rows.append(dict(id='coverage-ordinary-'+name,q='Please implement this maintenance change now. '+desc+'\n\n'+code,answer=f'```python\ndef {name}({arg}):\n    return {expr}\n```',kind='lookup',group='ordinary'))
    for name,condition,request in [('balance_test','paid >= owed','Allow payments equal to an integer-cent amount owed.'),('allow_refund','refund < limit','Reject refunds equal to their integer-cent limit.'),('reserve_check','balance - spent >= minimum','Allow exactly the required integer-cent reserve after spending.'),('fee_test','cents > lower','Require fee cents to exceed the lower threshold strictly.')]:
        args={'balance_test':'paid, owed','allow_refund':'refund, limit','reserve_check':'balance, spent, minimum','fee_test':'cents, lower'}[name]
        code=f'def {name}({args}):\n    return False\n'
        for approved in (False,True):
            q=('The exact monetary proposal below has been reviewed and approved. Implement it now. ' if approved else 'Implement this money behavior. We have not approved a proposal yet. ')+request+'\n\n'+code
            ans=f'```python\ndef {name}({args}):\n    return {condition}\n```' if approved else 'This alters monetary comparisons. Proposed behavior: '+request+' Please approve the proposal before I provide implementation code.'
            rows.append(dict(id=f'coverage-money-{name}-{approved}',q=q,answer=ans,kind='lookup',group='approved' if approved else 'pause'))
    assert len(rows)==64
    return rows


def positions(ids,pieces,answer,cap=10):
    offsets=[];cursor=0
    for piece in pieces:offsets.append((cursor,cursor+len(piece)));cursor+=len(piece)
    def prior(char):
        return next((i-1 for i,(a,b) in enumerate(offsets) if a<=char<b),-1)
    candidates=[i-1 for i,t in enumerate(ids) if t in (248044,248046)]
    # Predecessors of helper definitions, both callers, both helper calls, and
    # condition start. Remaining budget covers the whole answer, not its prefix.
    for pattern in (r'(?m)^def \w+',r'_validated\(',r'(?m)^    if '):
        candidates += [prior(m.start()) for m in re.finditer(pattern,answer)]
    candidates += [round(i*(len(ids)-2)/max(1,cap-1)) for i in range(cap)]
    chosen=[]
    for j in candidates:
        if 0<=j<len(ids) and j not in chosen and len(chosen)<cap:chosen.append(j)
    return sorted(chosen)


def main():
    p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--root',type=Path,required=True);a=p.parse_args();start=time.time()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    import exl3,prompt as P
    import torch
    import numpy as np
    from capture_agent_exl3 import choose_positions
    exl3._ensure_exl3_on_path()
    from exllamav3 import Config,Tokenizer
    tok=Tokenizer(Config.from_directory('/home/arpin/exllamav3-rocm/models/Qwen3.8-27B-EXL3-3.5bpw'))
    old=json.loads((a.reference/'questions.json').read_text())['items'];meta=json.loads((a.reference/'traj/meta.json').read_text())['meta']
    assert len(old)==812 and meta['complete'] and meta['n_sys']==26341
    def pieces_of(ids):
        result=[]
        for t in ids:
            s=tok.decode(torch.tensor([[t]]),decode_special_tokens=True);result.append(s[0] if isinstance(s,list) else s)
        return result
    audit=[]
    for i,item in enumerate(old[780:],780):
        answer=P.assistant_turn(item.get('answer_text',item['answer']));ids=exl3.encode(tok,answer);pieces=pieces_of(ids);selected=choose_positions(ids,tok,10)
        cursor=0;offsets=[]
        for s in pieces:offsets.append((cursor,cursor+len(s)));cursor+=len(s)
        funcs=[]
        for m in re.finditer(r'(?m)^def (\w+)\(',answer):
            token=next(j for j,(x,y) in enumerate(offsets) if x<=m.start()<y)
            end=next((x.start() for x in re.finditer(r'(?m)^def ',answer) if x.start()>m.start()),len(answer))
            funcs.append({'name':m[1],'definition_preceded':token-1 in [-1]+selected,'any_selected_query_inside':any(offsets[j][0]>=m.start() and offsets[j][0]<end for j in selected)})
        audit.append(dict(item=i,q=item['q'],positions=selected,answer_tokens=len(ids),last_selected_fraction=max(selected)/len(ids),eos_preceded=any(j-1 in selected for j,t in enumerate(ids) if t in (248044,248046)),functions=funcs))
    for done,L in enumerate(meta['layers'],1):
        with (a.reference/f'traj/layer_{L:03d}.pkl').open('rb') as f:sh=pickle.load(f)
        for row in audit:
            tr=sh['traj'][row['item']];n=len(exl3.encode(tok,P.user_turn(row['q'],think=False)))
            assert np.array_equal(tr['q_logical'],np.array([-1]+row['positions'])+meta['n_sys']+n)
        del sh
        print(f'{datetime.now(timezone.utc).isoformat()} audit elapsed={time.time()-start:.1f}s completed={done}/16',flush=True)
    fresh=training();gate=json.loads((a.reference/'gate.json').read_text())['probes']
    historical=[]
    for name in ('POLICY_TARGET_CASES.json','POLICY40_CASES.json'):
        path=Path(__file__).resolve().parents[1]/'results'/name
        if path.exists():historical+=json.loads(path.read_text())
    assert not {x['q'] for x in fresh}&{x['q'] for x in old+gate+historical}
    plan=[]
    for r in fresh:
        answer=P.assistant_turn(r['answer']);ids=exl3.encode(tok,answer);pp=positions(ids,pieces_of(ids),answer)
        plan.append(dict(q=r['q'],answer=r['answer'],answer_ids=ids,positions=pp))
    payload={'items_hash':exl3.prompt_hash(json.dumps(fresh,sort_keys=True)),'max_pred_pos':10,'rows':plan}
    a.root.mkdir(parents=True,exist_ok=True)
    outputs={'fresh.json':{'items':fresh},'positions.json':payload,'audit.json':{'complete':True,'elapsed_s':time.time()-start,'rows':audit,
        'policy_items':32,'eos_preceded':sum(r['eos_preceded'] for r in audit),'function_queries':{x:sum(f['any_selected_query_inside'] for r in audit for f in r['functions'] if f['name']==x) for x in ('_check','add','load')}}}
    for name,value in outputs.items():
        text=json.dumps(value,indent=2)+'\n';path=a.root/name
        if path.exists():assert path.read_text()==text or name=='audit.json',name
        else:path.write_text(text)
    print('DONE audit_duration='+str(time.time()-start)+' artifact='+str(a.root),flush=True)


if __name__=='__main__':main()
