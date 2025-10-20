


class DataMount:
    prefix: Path

    def path_exists(self, storage_type, path) -> bool:
        return Path(prefix, storage_type, path).exists()

    def link_path(self, storage_type, path) -> Path:

