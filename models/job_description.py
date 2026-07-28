"""Compatibility import for the authoritative JobDescription model.

New code must import ``JobDescription`` from ``JD.jd_model``. This module is
kept temporarily so older imports do not create a second incompatible model.
"""
from JD.jd_model import JobDescription

__all__ = ["JobDescription"]
