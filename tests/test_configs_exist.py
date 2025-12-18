import pathlib


def test_rg_swarm_config_exists() -> None:
    """Ensure default rg-swarm.yaml configuration is present."""
    root = pathlib.Path(__file__).resolve().parents[1]
    config_path = root / "rgym_exp" / "config" / "rg-swarm.yaml"
    assert config_path.is_file(), f"Config file is missing: {config_path}"
