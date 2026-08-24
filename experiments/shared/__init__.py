"""The fairness domain: constants every evaluated system MUST share, held once.

``workload.py`` (offered load), ``model.py`` (model + revision pin), and
``platform.py`` (GPU / engine geometry) define what "same conditions" means
for the matched-system comparison. System-specific controls such as KV
eviction, KV prefetching, and release slots stay in that system's ``config.py``
and never live here.
"""
