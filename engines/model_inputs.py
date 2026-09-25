"""Model-specific prompts for the periodic audio-input/text-output harness.

This layer does not own KV policy. Native audio-output/duplex pipelines are
different workload adapters and cannot be claimed by selecting a model here.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class AudioInputAdapter:
    family: str
    head: str
    audio: str
    instruction: str
    assistant: str
    continuation: str
    min_audio_ms: int

    def prompt(self, first):
        return (self.head + self.audio + self.instruction + self.assistant
                if first else self.continuation)

    def preload(self, text):
        return self.head + text + self.instruction + self.assistant


def audio_adapter(family):
    head = '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n'
    instruction = ' Listen to the audio and answer any question in it.'
    assistant = '<|im_end|>\n<|im_start|>assistant\n'
    if family == 'qwen25_omni':
        audio = '<|audio_bos|><|AUDIO|><|audio_eos|>'
        return AudioInputAdapter(family, head, audio, instruction, assistant, audio + '\n', 40)
    if family == 'minicpm_o45':
        # Placeholder is declared by the pinned vLLM MiniCPMO processor.
        # Explicitly close thinking as in the checkpoint's instruct template.
        audio = '(<audio>./</audio>)'
        assistant += '<think>\n\n</think>\n\n'
        continuation = '<|im_end|>\n<|im_start|>user\n' + audio + instruction + assistant
        return AudioInputAdapter(family, head, audio, instruction, assistant, continuation, 100)
    raise ValueError(f'unsupported audio model adapter: {family}')
