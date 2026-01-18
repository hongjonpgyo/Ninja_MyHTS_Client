class FavoriteManager:
    def __init__(self):
        self._favorites = set()

    def add(self, code: str):
        self._favorites.add(code)

    def remove(self, code: str):
        self._favorites.discard(code)

    def is_favorite(self, code: str) -> bool:
        return code in self._favorites

    def all(self):
        return list(self._favorites)
