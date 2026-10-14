# Optional: NS-3 / Aqua-Sim NG

**Application-level virtual simulation (this project's main app)** models signals, filters, link budget and routing in Python.
**Network-level NS-3/Aqua-Sim NG simulation** models protocol stacks (MAC, routing, queues, energy, channel models) at packet level, in C++.

They answer different questions, so NS-3 is deliberately NOT inside the Streamlit app (heavy build, not deployable on Streamlit Cloud).

## What is provided
* `export_topology.py` - writes `topology_nodes.csv` / `topology_links.csv` from the same virtual network (positions, ranges, feasible links with our channel's SNR/PER).
  Run: `python ns3/export_topology.py`. Already run once; the CSVs are included.

## What is NOT provided
No NS-3 scenario code and **no NS-3 results**. Writing one from memory would risk an API mismatch with your installed Aqua-Sim NG version.

## Suggested path
1. Install ns-3 and Aqua-Sim NG (https://github.com/rmartin5/aqua-sim-ng) following its README.
2. Start from one of its shipped examples (in its `examples/` folder), not from scratch.
3. Create nodes at the coordinates in `topology_nodes.csv`; use an acoustic broadcast/routing example; set the same modem range.
4. Compare *qualitatively* (hop count, delivery ratio, delay trend). Numbers will differ because the channel/MAC models differ - say so in your report.
