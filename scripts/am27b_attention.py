"""Session-local additive-prefix bias for EXL3; upstream files stay unchanged."""
from contextlib import contextmanager
import torch


def attend(q, k, v, beta, past, scale):
    if q.shape[0] != 1 or k.shape[0] != 1 or q.shape[2] % k.shape[2]:
        raise ValueError('AM wrapper requires batch1 and integral GQA')
    length, heads = q.shape[1:3]
    if beta.ndim != 2 or beta.shape[0] != k.shape[2] or beta.shape[1] > past:
        raise ValueError('invalid prefix beta shape')
    if k.shape[1] != past + length or v.shape != k.shape:
        raise ValueError('invalid occupied KV length')
    output_dtype = q.dtype
    if v.dtype != q.dtype:
        if v.dtype != torch.float32:
            raise ValueError('only FP32 value promotion supported')
        q, k = q.float(), k.float()
    group = heads // k.shape[2]
    bias = torch.zeros(heads, length, k.shape[1], device=q.device, dtype=q.dtype)
    bias[:, :, :beta.shape[1]] = beta.repeat_interleave(group, 0)[:, None].to(q.dtype)
    future = torch.arange(k.shape[1], device=q.device)[None] > (past + torch.arange(length, device=q.device))[:, None]
    bias.masked_fill_(future[None], float('-inf'))
    out = torch.nn.functional.scaled_dot_product_attention(q.transpose(1, 2),
        k.transpose(1, 2).repeat_interleave(group, 1),
        v.transpose(1, 2).repeat_interleave(group, 1), attn_mask=bias[None], scale=scale)
    out = out.transpose(1, 2).to(output_dtype).contiguous()
    if v.dtype != output_dtype and not torch.isfinite(out).all():
        raise ValueError('nonfinite FP32 attention output after native cast')
    return out


def load_fp32_prefix(folder, slots, device='cuda:0'):
    """Keep fitted V outside native FP16 cache; install zero placeholders only."""
    import json
    from safetensors.torch import load_file
    manifest = json.loads((folder/'manifest.json').read_text())
    if not manifest['complete'] or manifest['slots'] != slots or manifest['recipe'].get('values_dtype') != 'float32':
        raise ValueError('wrong FP32 AM manifest')
    if manifest['layers'] != list(range(3,64,4)):
        raise ValueError('incomplete FP32 AM layers')
    compiled, biases, values = {}, {}, {}
    for l in manifest['layers']:
        d = load_file(str(folder/f'layer_{l:03d}.safetensors'))
        if d['k'].shape != (1,4,slots,256) or d['v'].shape != d['k'].shape or d['beta'].shape != (1,4,slots):
            raise ValueError('invalid FP32 AM shapes')
        if d['k'].dtype != torch.float16 or d['v'].dtype != torch.float32 or d['beta'].dtype != torch.float16 or not all(torch.isfinite(t).all() for t in d.values()):
            raise ValueError('invalid FP32 AM dtype or values')
        compiled[l] = dict(k=d['k'], v=torch.zeros_like(d['k']))
        biases[l] = d['beta'][0].to(device)
        values[l] = d['v'].transpose(1,2).contiguous().to(device)
    return compiled, biases, values


@contextmanager
def prefix_bias(betas, prefix_values=None):
    import exllamav3.modules.attn as module
    prefix_values = {} if prefix_values is None else prefix_values
    for index, values in prefix_values.items():
        if index not in betas or values.dtype != torch.float32 or values.ndim != 4 or values.shape[0] != 1 or values.shape[1:3] != (betas[index].shape[1], betas[index].shape[0]) or not torch.isfinite(values).all():
            raise ValueError('invalid FP32 prefix values')
    original, bc = module.attn_dispatch, module._bc_attn_enable

    def dispatch(**kw):
        layer_index = kw.get('cache_idx')
        if layer_index not in betas:
            return original(**kw)
        if not kw['causal'] or kw.get('window_size') not in (None, -1) or kw.get('softcap') or kw.get('sinks') is not None or kw.get('non_causal_spans'):
            raise ValueError('unsupported AM attention mode')
        q, k, v = (kw[n] for n in ('q', 'k', 'v'))
        table, lengths = kw['block_table'], kw['cache_seqlens']
        if lengths.numel() != 1:
            raise ValueError('AM wrapper requires a single sequence')
        past = int(lengths.item())
        layer = kw['cache'].layers[layer_index, kw.get('cache_instance') or 0]
        pages = (past + q.shape[1] + layer.k.shape[1] - 1) // layer.k.shape[1]
        if not torch.equal(table[0, :pages].long(), torch.arange(pages, device=table.device)):
            raise ValueError('AM wrapper requires contiguous identity block table')
        layer.update_kv_direct(lengths, table, k, v, q.shape[1])
        occupied = past + q.shape[1]
        keys = layer.k.flatten(0, 1)[:occupied][None]
        values = layer.v.flatten(0, 1)[:occupied][None]
        if layer_index in prefix_values:
            saved = prefix_values[layer_index].to(q.device)
            if saved.shape[-1] != values.shape[-1] or saved.shape[1] > past:
                raise ValueError('FP32 prefix values overlap live rows')
            values = torch.cat((saved, values[:, saved.shape[1]:].float()), dim=1)
        return attend(q, keys, values, betas[layer_index].to(q.device), past, kw['sm_scale'])

    module.attn_dispatch, module._bc_attn_enable = dispatch, False
    try:
        yield
    finally:
        module.attn_dispatch, module._bc_attn_enable = original, bc
