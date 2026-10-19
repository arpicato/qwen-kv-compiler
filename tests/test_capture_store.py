"""CPU-only regression checks for bounded capture checkpoints and old shard parity."""
import json
from array import array
from pathlib import Path
import pickle
import tempfile
import tracemalloc
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from capture_store import CaptureStore


def main():
    with tempfile.TemporaryDirectory(dir='/tmp/opencode') as tmp:
        root=Path(tmp);layers=[3,7];schema='v2-causal-occupied'
        store=CaptureStore(root,layers,schema)
        for layer in layers:store.write_prefix(layer,{'k_sys':[layer], 'v_sys':[-layer]})
        index=[]
        expected={layer:[] for layer in layers}
        for start in (0,2,4):
            pending={layer:[{'item':i,'q_rot':array('f',[float(i),-0.0,layer]),'q':str(i)} for i in range(start,start+2)] for layer in layers}
            for layer in layers:expected[layer]+=pending[layer]
            index += [{'item':i,'q':str(i)} for i in range(start,start+2)]
            store.checkpoint(pending,{'meta':{'complete':False},'index':index})
            assert all(not rows for rows in pending.values()), 'must release every batch'
            if start==0:
                first={layer:(root/f'capture/layer_{layer:03d}.stream').read_bytes() for layer in layers}
            else:
                for layer in layers:
                    assert (root/f'capture/layer_{layer:03d}.stream').read_bytes().startswith(first[layer]), 'rewrote an earlier batch'
        saved=json.loads((root/'meta.json').read_text())
        sizes={layer:(root/f'capture/layer_{layer:03d}.stream').stat().st_size for layer in layers}
        # Crash after writing one layer, before metadata commit: uncommitted tail
        # must not become visible and must be discarded on the next append.
        with (root/'capture/layer_003.stream').open('ab') as f:pickle.dump([{'item':6,'bad':True}],f)
        resumed=CaptureStore(root,layers,schema,saved['storage'])
        resumed.validate(6)
        assert resumed.offsets=={str(k):v for k,v in sizes.items()}
        pending={layer:[{'item':6,'q_rot':b'last','q':'6'}] for layer in layers}
        index.append({'item':6,'q':'6'})
        resumed.checkpoint(pending,{'meta':{'complete':False},'index':index})
        for layer in layers:expected[layer].append({'item':6,'q_rot':b'last','q':'6'})
        progress=[]
        resumed.finalize(7,lambda layer:progress.append(layer))
        assert progress==layers
        for layer in layers:
            with (root/f'layer_{layer:03d}.pkl').open('rb') as f:shard=pickle.load(f)
            assert shard=={'schema':schema,'k_sys':[layer],'v_sys':[-layer],'traj':expected[layer]}
            for actual,want in zip(shard['traj'],expected[layer]):
                if isinstance(want['q_rot'],array):assert actual['q_rot'].tobytes()==want['q_rot'].tobytes()
        # Repeat finalization after interruption: deterministic compatibility output.
        resumed.finalize(7,lambda layer:None)
        # A checkpoint failure cannot mutate the last published offset manifest.
        before=(root/'meta.json').read_bytes()
        try:resumed.checkpoint({3:[{'item':7}],7:[]},{'meta':{},'index':index})
        except ValueError:pass
        else:raise AssertionError('inconsistent batch accepted')
        assert (root/'meta.json').read_bytes()==before
        state=json.loads(before)['storage']
        (root/'capture/layer_007.stream').write_bytes(b'')
        try:CaptureStore(root,layers,schema,state).validate(7)
        except ValueError:pass
        else:raise AssertionError('truncated committed shard accepted')
    with tempfile.TemporaryDirectory(dir='/tmp/opencode') as tmp:
        store=CaptureStore(tmp,[3,7],schema)
        tracemalloc.start()
        for i in range(32):
            pending={layer:[{'item':i,'blob':bytes([i])*262144}] for layer in (3,7)}
            store.checkpoint(pending,{'meta':{'complete':False},'index':[{'item':j} for j in range(i+1)]})
        current,peak=tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert current<1048576 and peak<3145728,(current,peak)
        assert sum(store.offsets.values())>16*1000*1000
        print(f'Bounded-memory fixture: >16MB captured, Python current={current}B peak={peak}B')
    print('PASS bounded batch release, append-only checkpoints, crash-tail resume, truncation rejection and bit-preserving legacy shard output')


if __name__=='__main__':main()
