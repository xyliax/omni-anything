"""The fairness domain: constants both arms MUST share, held once.

``workload.py`` (offered load), ``model.py`` (model + revision pin), and
``platform.py`` (GPU / engine geometry) define what "same conditions" means
for the two-arm comparison. Arm-behavior knobs (park, prefetch, slots, ...)
are private to each arm's ``config.py`` and never live here.
"""
