import asgi
from workers import WorkerEntrypoint

from app import app
from core.context import worker_env


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        token = worker_env.set(self.env)
        try:
            return await asgi.fetch(app, request, self.env)
        finally:
            worker_env.reset(token)
