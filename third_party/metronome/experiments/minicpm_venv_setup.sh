#!/bin/bash
# MiniCPM-o-4.5 native streaming needs transformers 4.51 (its target) + a MATCHED cu128 torch stack
# for Blackwell + the minicpmo package and its deps. Run the streaming proto with this venv's python.
set -e
uv venv ~/mcpm-venv --python 3.10
export VIRTUAL_ENV=~/mcpm-venv
uv pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/cu128
uv pip install "transformers==4.51.0" accelerate soundfile numpy librosa sentencepiece
uv pip install minicpmo einops vocos vector-quantize-pytorch onnx onnxruntime hyperpyyaml diffusers
# run:  ~/mcpm-venv/bin/python experiments/minicpm_streaming_proto.py
