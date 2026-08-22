# AEO benchmark

This directory contains the reproducible five-portal agent benchmark.

The execution contract is:

1. `self_check.py` validates the canonical query bank and configuration.
2. `ollama_multiagent.py` freezes evidence per query/portal and executes the local multi-agent workflow.
3. `analyze_results.py` summarizes results and computes portal-level association statistics.
4. `analyze_agent_benchmark.py` provides a compact statistical report from the same results schema.

Do not treat repeated model runs as independent portal observations. The experimental unit for portal-level association is the portal; query and repeat are clustered/repeated measures.

The final PowerPoint must be rebuilt after validated benchmark results are collected.
