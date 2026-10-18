"""Hydra-based training entry point skeleton."""

import hydra
from omegaconf import DictConfig


@hydra.main(version_base=None, config_path="../../configs", config_name="ml_config")
def main(config: DictConfig) -> None:
    """Run model training using the selected Hydra configuration."""
    _ = config
    print("Entraînement en cours...")
    # TODO: Implement data loading, training, and checkpointing.


if __name__ == "__main__":
    main()
