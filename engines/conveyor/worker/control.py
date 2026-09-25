"""Run-boundary controls; never invoked on a timer inside business traffic."""
import argparse
import sys
from pathlib import Path

import grpc

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'third_party/metronome/worker'))
import inference_pb2 as pb
import inference_pb2_grpc as rpc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--address', required=True)
    parser.add_argument('--action', choices=('gpu_trace_start', 'gpu_trace_stop'), required=True)
    args = parser.parse_args()
    with grpc.insecure_channel(args.address) as channel:
        rpc.InferenceStub(channel).Step(pb.StepRequest(), timeout=290,
            metadata=(('x-pilarius-control', args.action),))
    print(args.action + ' completed', flush=True)


if __name__ == '__main__':
    main()
