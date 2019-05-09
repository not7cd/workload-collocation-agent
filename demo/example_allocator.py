from dataclasses import dataclass
from wca.allocators import Allocator, RDTAllocation, Metric
from wca.detectors import ContentionAnomaly, ContendedResource
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
    """Simple allocator that watches over MPKI (cache misses per kilo instruction) of
    latency-critical tasks, and reacts by throttling best-effort tasks. """

    mpki_threshold: float = 1.

    def allocate(self, platform, measurements, resources, labels, allocations):

        be_tasks = [t for t in labels if labels[t].get('task_kind') == 'best-effort']
        lc_tasks = [t for t in labels if labels[t].get('task_kind') == 'latency-critical']

        log.debug('Found %s latency-critical tasks and %s best-effort tasks',
                  len(lc_tasks), len(be_tasks))

        # Calculate IPC accorss all latency critical tasks...
        anomalies = []
        mpki = 0
        for task in lc_tasks:
            if 'cache_misses_per_kilo_instructions' in measurements[task]:
                mpki += measurements[task]['cache_misses_per_kilo_instructions']
                if mpki < self.mpki_threshold:
                    anomalies.append(
                        ContentionAnomaly(
                            resource=ContendedResource.LLC,
                            contended_task_id=task,
                            contending_task_ids=be_tasks,
                            metrics=[
                                Metric(name='lc_mpki', value=mpki)
                            ]
                        )
                    )

        new_allocations = {}
        # Thortlle or enable best-efforts tasks based on preasure.
        if be_tasks and lc_tasks:
            if mpki > self.mpki_threshold and mpki > 0:
                allocation = THROTTLE
                log.info('mpki=%r -> thorttle %s best-effort tasks', mpki, len(be_tasks))
            else:
                allocation = ENABLE
                log.info('mpki=%r -> enable %s best-effort tasks', mpki, len(be_tasks))

            new_allocations = {t: allocation for t in be_tasks}

        return new_allocations, anomalies, [
            Metric(name='example_allocator_mpki', value=mpki,
                   labels=dict(kind='current')),
            Metric(name='example_allocator_mpki', value=self.mpki_threshold,
                   labels=dict(kind='threshold')),
        ]
