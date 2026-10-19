"""Append-only capture batches; publish offsets atomically before legacy export."""
import json
import os
from pathlib import Path
import pickle


class CaptureStore:
    def __init__(self, root, layers, schema, state=None):
        self.root=Path(root)
        self.layers=list(layers)
        self.schema=schema
        self.directory=self.root/'capture'
        self.directory.mkdir(parents=True,exist_ok=True)
        self.offsets={str(layer):0 for layer in layers}
        if state is not None:
            if state.get('format')!='append-pickle-v1' or set(state['offsets'])!=set(self.offsets):
                raise ValueError('capture storage identity differs')
            if any(type(n) is not int or n<0 for n in state['offsets'].values()):
                raise ValueError('invalid capture offsets')
            self.offsets=dict(state['offsets'])

    def path(self,layer):return self.directory/f'layer_{layer:03d}.stream'

    def write_prefix(self,layer,prefix):
        path=self.directory/f'prefix_{layer:03d}.pkl'
        partial=path.with_suffix('.partial')
        with partial.open('wb') as f:
            pickle.dump(dict(prefix,schema=self.schema),f,protocol=pickle.HIGHEST_PROTOCOL)
            f.flush();os.fsync(f.fileno())
        partial.replace(path)

    def append(self,layer,rows):
        path=self.path(layer);offset=self.offsets[str(layer)]
        if offset and (not path.exists() or path.stat().st_size<offset):
            raise ValueError('truncated committed capture')
        with path.open('r+b' if path.exists() else 'w+b') as f:
            f.truncate(offset);f.seek(offset)
            if rows:pickle.dump(rows,f,protocol=pickle.HIGHEST_PROTOCOL)
            f.flush();os.fsync(f.fileno())
            self.offsets[str(layer)]=f.tell()

    def batches(self,layer):
        end=self.offsets[str(layer)]
        if end==0:return
        path=self.path(layer)
        if not path.exists() or path.stat().st_size<end:
            raise ValueError('truncated committed capture')
        with path.open('rb') as f:
            while f.tell()<end:
                try:batch=pickle.load(f)
                except (EOFError,pickle.UnpicklingError) as err:
                    raise ValueError('invalid committed capture batch') from err
                if f.tell()>end or not isinstance(batch,list):
                    raise ValueError('capture offset does not delimit a batch')
                yield batch

    def validate(self,count):
        for layer in self.layers:
            seen=0
            for batch in self.batches(layer):
                if [row['item'] for row in batch]!=list(range(seen,seen+len(batch))):
                    raise ValueError('capture items out of order')
                seen+=len(batch)
            if seen!=count:raise ValueError('capture count differs from checkpoint')

    def checkpoint(self,pending,payload):
        sizes=[len(pending[layer]) for layer in self.layers]
        if len(set(sizes))!=1:raise ValueError('inconsistent per-layer batch counts')
        for layer in self.layers:self.append(layer,pending[layer])
        data=dict(payload,storage={'format':'append-pickle-v1','offsets':dict(self.offsets)})
        path=self.root/'meta.json';partial=path.with_suffix('.partial')
        with partial.open('w') as f:
            json.dump(data,f,indent=2);f.flush();os.fsync(f.fileno())
        partial.replace(path)
        for rows in pending.values():rows.clear()

    def finalize(self,count,progress):
        # ponytail: capture memory is bounded by one batch; compatibility export
        # still materializes ONE layer. Compiler stays unchanged. A future lazy
        # compiler reader can remove this per-layer ceiling if it becomes limiting.
        for layer in self.layers:
            with (self.directory/f'prefix_{layer:03d}.pkl').open('rb') as f:shard=pickle.load(f)
            traj=[]
            for batch in self.batches(layer):traj.extend(batch)
            if len(traj)!=count:raise ValueError('incomplete layer at export')
            shard['traj']=traj
            path=self.root/f'layer_{layer:03d}.pkl';partial=path.with_suffix('.pkl.partial')
            with partial.open('wb') as f:
                pickle.dump(shard,f,protocol=pickle.HIGHEST_PROTOCOL)
                f.flush();os.fsync(f.fileno())
            partial.replace(path)
            del shard,traj
            progress(layer)
