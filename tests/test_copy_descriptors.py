import sys
import unittest
import ctypes
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engines/conveyor/worker/engine_patch'))
from copy_descriptors import contiguous_runs
import copy_descriptors


class MappingTests(unittest.TestCase):
    def test_coalescing_preserves_mapping_with_fragmented_and_reordered_ids(self):
        source, target = [7,1,2,8,12,13], [20,10,11,21,30,32]
        runs = contiguous_runs(source, target)
        expanded = [(s+i,d+i) for s,d,n in runs for i in range(n)]
        self.assertEqual(expanded, sorted(zip(source,target)))
        self.assertEqual(len(runs), 4)
        self.assertEqual(contiguous_runs(list(range(128)),list(range(128))), [[0,0,128]])

    def test_duplicate_destination_fails_before_any_dma(self):
        with self.assertRaises(ValueError):
            contiguous_runs([1,2],[3,3])

    def test_fragmented_copy_is_bounded_and_covers_every_mapping_once(self):
        observed = []
        def submit(dst, src, sizes, count, *rest):
            array = ctypes.c_uint64 * count
            observed.append(list(zip(array.from_address(src), array.from_address(dst), array.from_address(sizes))))
            return 0
        params = SimpleNamespace(src_bases=[1000,10000,20000], dst_bases=[30000,40000,50000],
            bpb=[8,8,8], attrs=ctypes.c_uint(1), attrs_idx=ctypes.c_size_t(0),
            fail_idx=ctypes.c_size_t(0), stream_handle=1)
        native = SimpleNamespace(cuda_mem_ops=SimpleNamespace())
        modules = {'vllm.v1.simple_kv_offload':native,
                   'vllm.platforms':SimpleNamespace(current_platform=SimpleNamespace(is_rocm=lambda:False))}
        source, target = list(range(0,256,2)), list(range(1,257,2))
        with patch.dict(sys.modules, modules), patch.object(copy_descriptors,'_submit',submit):
            stat = copy_descriptors.copy_blocks(source,target,params,batch_limit=128)
        self.assertEqual([len(batch) for batch in observed],[128,128,128])
        expected = [(sb+s*8, db+d*8, 8) for sb,db in zip(params.src_bases,params.dst_bases) for s,d in zip(source,target)]
        self.assertEqual([entry for batch in observed for entry in batch], expected)
        self.assertEqual(stat['copy_descriptors'],384)
