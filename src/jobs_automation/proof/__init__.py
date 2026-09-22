"""Proof-integrity helpers shared by the V1.4 real-proof producer and consumer.

Both ``scripts/run_v14_real_proof.py`` (producer) and ``scripts/verify_v14_real_proof.py``
(consumer) import from here so that the private evidence bundle never carries a
database credential and so that the same normalized candidate-profile fingerprint is
computed on both sides.
"""
