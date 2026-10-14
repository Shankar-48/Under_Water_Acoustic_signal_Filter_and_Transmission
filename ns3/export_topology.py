"""Export our virtual topology so the SAME network can be rebuilt in NS-3 / Aqua-Sim NG.
Writes ns3/topology_nodes.csv and ns3/topology_links.csv (links that our channel model considers feasible).
This script does NOT run NS-3 and produces no NS-3 results."""
import csv, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from simulation.environment import Environment
from simulation.routing import build_links

env = Environment()
with open(ROOT / "ns3" / "topology_nodes.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id", "type", "x_m", "y_m", "z_m", "range_m"])
    for n in env.nodes.values(): w.writerow([n.node_id, n.node_type, *map(lambda v: round(float(v), 1), n.position), n.comm_range])
with open(ROOT / "ns3" / "topology_links.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["tx", "rx", "distance_m", "snr_db", "per"])
    for reps in build_links(env.nodes, env.channel).values():
        for r in reps: w.writerow([r["tx"], r["rx"], round(r["distance_m"], 1), round(r["snr_db"], 2), f"{r['per']:.3e}"])
print("Wrote ns3/topology_nodes.csv and ns3/topology_links.csv")
