"""Lossless coalescing of physical block mappings before CUDA submission.

Only adjacent source AND destination blocks can share a descriptor. The
per-layer strides and original mapping are preserved; no staging buffer,
packing kernel, extra copy, or data-format change is involved.
"""
from __future__ import annotations

import ctypes
import time

_submit = None


class DriverEvents:
    """Short, nonblocking driver calls keep the GIL across submission.

    ctypes.CFUNCTYPE and torch event/stream wrappers can release the GIL. A
    busy Python model-control thread can then delay *reacquiring* it between
    event-record and memcpy by a full interpreter time slice. These calls
    only enqueue/query; none synchronizes a stream or waits for a DMA.
    """
    def __init__(self):
        self.lib = ctypes.PyDLL('libcuda.so.1')
        ptr = ctypes.c_void_p
        for name, args in {
            'cuEventCreate': [ctypes.POINTER(ptr), ctypes.c_uint],
            'cuEventRecord': [ptr, ptr], 'cuEventQuery': [ptr],
            'cuEventElapsedTime': [ctypes.POINTER(ctypes.c_float), ptr, ptr],
            'cuEventDestroy_v2': [ptr],
        }.items():
            fn = getattr(self.lib, name)
            fn.argtypes, fn.restype = args, ctypes.c_uint

    @staticmethod
    def check(code):
        if code:
            raise RuntimeError(f'CUDA event API failed: {code}')

    def create(self):
        event = ctypes.c_void_p()
        self.check(self.lib.cuEventCreate(ctypes.byref(event), 0))
        return event

    def record(self, event, stream):
        self.check(self.lib.cuEventRecord(event, stream))

    def finished(self, event):
        code = self.lib.cuEventQuery(event)
        if code == 600:  # CUDA_ERROR_NOT_READY
            return False
        self.check(code)
        return True

    def elapsed_and_destroy(self, handle):
        value = ctypes.c_float()
        self.check(self.lib.cuEventElapsedTime(ctypes.byref(value), *handle))
        for event in handle:
            self.check(self.lib.cuEventDestroy_v2(event))
        return value.value


def contiguous_runs(sources, targets):
    if len(sources) != len(targets) or not sources:
        raise ValueError('nonempty matching block lists required')
    if len(set(targets)) != len(targets) or min(sources) < 0 or min(targets) < 0:
        raise ValueError('destinations must be unique and block IDs nonnegative')
    runs = []
    for source, target in sorted(zip(sources, targets)):
        if runs and source == runs[-1][0] + runs[-1][2] and target == runs[-1][1] + runs[-1][2]:
            runs[-1][2] += 1
        else:
            runs.append([source, target, 1])
    return runs


def copy_blocks(sources, targets, params, *, batch_limit=128):
    """Bound driver setup before the first DMA even for fragmented mappings.

    Pinned source/target ownership is held by CopyService until its end event.
    Stream ordering is sufficient; descriptors may execute out of order inside
    a batch, exactly as in the backend's original batch-copy implementation.
    """
    global _submit
    from vllm.v1.simple_kv_offload import cuda_mem_ops as native
    from vllm.platforms import current_platform

    if batch_limit < 1:
        raise ValueError('positive descriptor batch limit required')
    begin = time.perf_counter()
    runs = contiguous_runs(sources, targets)
    # Keep setup bounded before the first enqueue, even when no adjacent
    # mappings exist. Python integers avoid NumPy releasing the GIL here.
    layers = list(zip(map(int, params.src_bases), map(int, params.dst_bases), map(int, params.bpb)))
    total = len(layers) * len(runs)
    array = ctypes.c_uint64 * min(batch_limit, total)
    src, dst, sizes = array(), array(), array()
    if _submit is None:
        prototype = ctypes.PYFUNCTYPE(ctypes.c_uint, *native._BATCH_MEMCPY_FUNC_TYPE._argtypes_)
        _submit = prototype(ctypes.cast(native._batch_memcpy_fn, ctypes.c_void_p).value)
    prepared = time.perf_counter()
    thread_begin = time.thread_time()
    first_end = None
    api_ms = api_thread_ms = 0.0
    for offset in range(0, total, batch_limit):
        count = min(batch_limit, total - offset)
        for j in range(count):
            layer, run = divmod(offset + j, len(runs))
            sb, db, stride = layers[layer]
            s, d, n = runs[run]
            src[j], dst[j], sizes[j] = sb + s * stride, db + d * stride, n * stride
        api_start, cpu_start = time.perf_counter(), time.thread_time()
        err = _submit(
            ctypes.addressof(dst), ctypes.addressof(src), ctypes.addressof(sizes), count,
            ctypes.addressof(params.attrs), ctypes.byref(params.attrs_idx),
            0 if current_platform.is_rocm() else 1,
            ctypes.byref(params.fail_idx), params.stream_handle)
        api_ms += (time.perf_counter() - api_start) * 1000
        api_thread_ms += (time.thread_time() - cpu_start) * 1000
        if err:
            raise RuntimeError(f'batch memcpy failed: err={err} descriptor={offset + params.fail_idx.value}')
        if first_end is None:
            first_end = time.perf_counter()
    ended = time.perf_counter()
    return dict(copy_descriptors=total, contiguous_runs=len(runs),
                copy_api_calls=(total + batch_limit - 1) // batch_limit,
                descriptor_prepare_ms=(prepared - begin) * 1000,
                copy_enqueue_ms=(ended - prepared) * 1000,
                copy_enqueue_thread_ms=(time.thread_time() - thread_begin) * 1000,
                copy_api_ms=api_ms, copy_api_thread_ms=api_thread_ms,
                first_batch_return_ms=(first_end - prepared) * 1000)
