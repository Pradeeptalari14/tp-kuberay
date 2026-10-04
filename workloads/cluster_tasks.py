"""Interactive task distribution across Ray worker nodes."""
import os
import socket
import ray

@ray.remote(num_gpus=1)
def gpu_task(task_id: int) -> dict:
    hostname = socket.gethostname()
    gpu_ids = ray.get_gpu_ids()
    return {
        "task_id": task_id,
        "node": hostname,
        "gpu_ids": gpu_ids,
        "status": "completed"
    }

if __name__ == "__main__":
    ray_address = os.environ.get("RAY_ADDRESS", "auto")
    print(f"Connecting to Ray at: {ray_address}")
    ray.init(address=ray_address)

    print("Submitting 16 GPU tasks to trigger KubeRay autoscaler...")
    futures = [gpu_task.remote(i) for i in range(16)]
    results = ray.get(futures)

    nodes = {r["node"] for r in results}
    print(f"Successfully processed {len(results)} tasks across {len(nodes)} distinct worker nodes:")
    for node in sorted(nodes):
        node_tasks = [r for r in results if r["node"] == node]
        print(f"  - Node {node}: executed {len(node_tasks)} tasks")
