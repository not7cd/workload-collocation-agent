from dataclasses import dataclass
from wca.allocators import Allocator, RDTAllocation, Metric
import logging
log = logging.getLogger(__name__)


# Predefined resources configuration.
THROTTLE = dict(
    cpu_quota=0.1,
    rdt=RDTAllocation(
        name='best-effort',
        l3='L3:0=002;1=002',
        mb='MB:0=10;1=10'
    )
)

ENABLE = dict(
    cpu_quota=1.,
    rdt=RDTAllocation(
        name='best-effort',
        l3='L3:0=ff;1=ff',
        mb='MB:0=100;1=100'
    )
)


@dataclass
class ExampleAllocator(Allocator):
    """Simple allocator that watches over IPC (instruction per cycles) of latency-critical tasks,
    and reacts by throttling best-effort tasks. """

    ipc_threshold: float = 1.
    preasure_threshold: float = 1.

    def allocate(self, platform, measurements, resources, labels, allocations):

        be_tasks = [t for t in labels if labels[t].get('task_kind') == 'best-effort']
        lc_tasks = [t for t in labels if labels[t].get('task_kind') == 'latency-critical']

        log.debug('Found %s latency-critical tasks and %s best-effort tasks',
                  len(lc_tasks), len(be_tasks))

        # Calculate IPC preasure ...
        preasure = 0.
        for task in lc_tasks:
            if 'ipc' in measurements[task]:
                ipc = measurements[task]['ipc']
                if ipc < self.ipc_threshold:
                    preasure += 1/ipc

        new_allocations = {}
        # Thortlle or enable best-efforts tasks based on preasure.
        if be_tasks:
            if preasure > self.preasure_threshold:
                allocation = THROTTLE
                log.info('Preasure=%r -> thorttle %s best-effort tasks', preasure, len(be_tasks))
            else:
                allocation = ENABLE
                log.info('Preasure=%r -> enable %s best-effort tasks', preasure, len(be_tasks))
            new_allocations = {t: allocation for t in be_tasks}
        else:
            new_allocations = {}

        return new_allocations, [], [Metric(name='total_preasure', value=preasure)]
