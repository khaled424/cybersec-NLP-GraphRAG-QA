"""Hydra entry point: extract entities, build the graph and the vector index."""

import hydra
from omegaconf import DictConfig


@hydra.main(version_base=None, config_path="../../../configs", config_name="pipeline_config")
def main(config: DictConfig) -> None:
    """Run the knowledge-base build using the selected Hydra configuration."""
    _ = config
    # TODO: Chain preprocessing -> NER -> knowledge graph -> vector index.
    print("TODO: build the knowledge base.")


if __name__ == "__main__":
    main()
