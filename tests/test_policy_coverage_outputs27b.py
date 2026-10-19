"""Validate authored calibration code before capture; no generated code on host."""
import argparse
import json
from pathlib import Path
import re
import subprocess


def main():
    p=argparse.ArgumentParser();p.add_argument('--items',type=Path,required=True);p.add_argument('--image',required=True);a=p.parse_args()
    items=json.loads(a.items.read_text())['items'];code=''
    for r in items:
        if r['group'] not in ('shared','distinct'):continue
        patch=re.search(r'```python\n(.*?)```',r['answer'],re.S)[1]
        supplied=r['q'].split('\n\n',1)[1];left,right=r['names']
        code+=f'''
namespace={{}};original={{}}
exec({patch!r},namespace);exec({supplied!r},original)
def capture(fn,x):
 try:return ('ok',fn(x))
 except ValueError:return ('error',None)
for value in {r['values']!r}:
 {r['argument']}=value
 invalid=bool({r['new_condition']})
 for name in {r['names']!r}:
  actual=capture(namespace[name],value)
  expected=capture(original[name],value) if ({r['group']=='distinct'!r} and name=={right!r}) or not invalid else ('error',None)
  assert actual==expected,({r['id']!r},name,value,actual,expected)
'''
    cmd=['docker','run','--rm','-i','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','32','--memory','128m','--cpus','1','--user','65534:65534','--entrypoint','/usr/bin/python3',a.image,'-I','-']
    r=subprocess.run(cmd,input=code,capture_output=True,text=True,timeout=30)
    assert r.returncode==0,r.stderr
    print('PASS40authoredshared/distinctcalibrationpatcheswithrealboundary/outputassertions',flush=True)


if __name__=='__main__':main()
