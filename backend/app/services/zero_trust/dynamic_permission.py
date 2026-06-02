"""Auto-generated stub."""


class PermissionEvaluator:
    async def evaluate(self, user, resource: str, action: str) -> bool:
        return True


permission_evaluator = PermissionEvaluator()
