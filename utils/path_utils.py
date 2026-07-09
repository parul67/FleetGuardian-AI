import os

class PathUtils:
    @staticmethod
    def get_project_root() -> str:
        """Returns the absolute path to the project root directory."""
        # path_utils.py is inside utils/ which is 1 levels deep from the root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.dirname(current_dir))

    @classmethod
    def resolve_path(cls, relative_path: str) -> str:
        """Resolves a path relative to the project root if it is not already absolute."""
        if os.path.isabs(relative_path):
            return os.path.normpath(relative_path)
        return os.path.normpath(os.path.join(cls.get_project_root(), relative_path))

    @classmethod
    def get_model_path(cls, model_filename: str) -> str:
        """Returns the absolute path to a model file located inside the models/ folder."""
        return cls.resolve_path(os.path.join("models", model_filename))

    @classmethod
    def get_config_path(cls, config_filename: str) -> str:
        """Returns the absolute path to a configuration file located inside the configs/ folder."""
        return cls.resolve_path(os.path.join("configs", config_filename))
