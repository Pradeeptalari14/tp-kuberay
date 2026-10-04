"""Distributed PyTorch training job executed by RayJob."""
import os
import ray
import ray.train
import ray.train.torch
from ray.train import ScalingConfig
from ray.train.torch import TorchTrainer

def train_loop_per_worker(config: dict) -> None:
    import torch
    import torch.nn as nn

    model = nn.Sequential(
        nn.Linear(32, 64),
        nn.ReLU(),
        nn.Linear(64, 1)
    )
    model = ray.train.torch.prepare_model(model)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.get("lr", 1e-3))
    loss_fn = nn.MSELoss()

    for epoch in range(config.get("epochs", 3)):
        inputs = torch.randn(64, 32)
        targets = torch.randn(64, 1)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = loss_fn(outputs, targets)
        loss.backward()
        optimizer.step()

        ray.train.report({"epoch": epoch + 1, "loss": loss.item()})
        print(f"[Worker] Epoch {epoch + 1}: Loss = {loss.item():.4f}")

if __name__ == "__main__":
    num_workers = int(os.environ.get("NUM_WORKERS", "2"))
    use_gpu = os.environ.get("USE_GPU", "false").lower() in ("true", "1")

    print(f"Starting TorchTrainer with {num_workers} workers (use_gpu={use_gpu})...")
    trainer = TorchTrainer(
        train_loop_per_worker=train_loop_per_worker,
        train_loop_config={"lr": 0.001, "epochs": 3},
        scaling_config=ScalingConfig(
            num_workers=num_workers,
            use_gpu=use_gpu
        )
    )

    results = trainer.fit()
    print("Training job complete!")
    print(f"Final metrics: {results.metrics}")
