"""A stand-in for the runtime's `run_process` that keeps each request it is handed."""

from factory.adapters.process import ProcessRequest, ProcessResult, run_process


class Recorder:
    """Keeps each request; answers with the next given result, or runs it once none is left."""

    def __init__(self) -> None:
        self.requests: list[ProcessRequest] = []
        self.results: list[ProcessResult] = []

    def __call__(self, request: ProcessRequest) -> ProcessResult:
        self.requests.append(request)
        if len(self.requests) <= len(self.results):
            return self.results[len(self.requests) - 1]
        return run_process(request)
