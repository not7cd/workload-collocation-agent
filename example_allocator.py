from dataclasses import dataclass
from owca.allocators import Allocator, RDTAllocation, Metric
import logging
log = logging.getLogger(__name__)

THROTTLE = {
    'cpu_quota': 0.,
    'rdt': RDTAllocation(
        name='best-effort',
        l3='L3:0=002;1=002',
        mb='MB:0=10;1=10'
    )
}

ENABLE = {
    'cpu_quota': 1.,
    'rdt': RDTAllocation(
        name='best-effort',
        l3='L3:0=ff;1=ff',
        mb='MB:0=100;1=100'
    )
}


@dataclass
class ExampleAllocator(Allocator):

    preasure_threshold: float = 1.

    def __post_init__(self):
        log.info('Example allocator with preasure_threshold: %r', self.preasure_threshold)

    def allocate(self, platform, measurements, resources, labels, allocations):

        # Calculate preasure ...
        total_preasure = 0.
        for task in measurements:
            if labels[task].get('task_kind') == 'latency-critical':
                ipc = measurements[task].get('ipc', 1.0)
                log.debug('found latency critical task with ipc: %r',  ipc)
                if ipc < 1.:
                    total_preasure += 1/measurements[task]['ipc']
        metrics = [
            Metric(name='total_preasure', value=total_preasure)
        ]

        new_allocations = {}
        # Thortlle or enable best-efforts tasks based on preasure.
        for task in measurements:
            if labels[task].get('task_kind') == 'best-effort':
                if total_preasure > self.preasure_threshold:
                    new_allocations[task] = THROTTLE
                else:
                    new_allocations[task] = ENABLE

        return new_allocations, [], metrics
