"""Package version service stub."""
class PackageVersionService:
    @staticmethod
    def check_version(): return {"latest": "1.0.0", "current": "1.0.0"}
    @staticmethod
    def parse_version(v):
        """Parse version string, return tuple of ints or original."""
        try:
            parts = v.split(".")
            if all(p.isdigit() for p in parts):
                return tuple(int(p) for p in parts)
        except Exception:
            pass
        return v

def get_version(self):
    """Backward-compat."""
    return {"latest": "1.0.0", "current": "1.0.0", "version": "1.0.0"}

def _parse_version(self, v):
    """Backward-compat."""
    return v

PackageVersionService.get_version = get_version
PackageVersionService._parse_version = _parse_version
