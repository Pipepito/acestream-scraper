"""Canonical application paths behind an ASGI mount or reverse-proxy prefix."""
def route_path(scope):
    path = scope.get('path', '')
    root = scope.get('root_path', '').rstrip('/')
    if root and (path == root or path.startswith(root + '/')):
        return path[len(root):] or '/'
    return path
