from dataclasses import dataclass
from wca.allocators import Allocator, RDTAllocation, Metric
from wca.detectors import ContentionAnomaly, ContendedResource
import logging
log = logging.getLogger(__name__)


# Predefined resources configuration for best-efforts tasks.
THROTTLE = dict(
    cpu_quota=0.01,
    rdt=RDTAllocation(
        name='best-effort',
        l3='L3:0=001;1=001',
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
    """Simple allocator that monitors some metric (defaults to cache misses per kilo instruction) 
    for latency-critical tasks, and reacts by throttling best-effort tasks. """

    threshold: float = 1.
    metric_name: str = 'ipc'
    _steady_duration: int = 10

    def allocate(self, platform, measurements, resources, labels, allocations):

        be_tasks = [t for t in labels if labels[t].get('task_kind') == 'best-effort']
        lc_tasks = [t for t in labels if labels[t].get('task_kind') == 'latency-critical']

        log.debug('Found %s latency-critical tasks and %s best-effort tasks',
                  len(lc_tasks), len(be_tasks))

        # Check value of metric accords all latency critical tasks...
        anomalies = []
        value = 0
        for task in lc_tasks:
            if self.metric_name in measurements[task]:
                value += measurements[task][self.metric_name]
                if value < self.threshold:
                    # Return information about found resource contention caused anomaly.
                    anomalies.append(
                        ContentionAnomaly(
                            resource=ContendedResource.LLC,
                            contended_task_id=task,
                            contending_task_ids=be_tasks,
                            metrics=[
                                Metric(name='lc_value', value=value)
                            ]
                        )
                    )

        # Throttle or enable best-efforts tasks based on number of cache misses.
        new_allocations = {}
        if be_tasks and lc_tasks:
            if value > 0:
                if value < self.threshold:
                    allocation = THROTTLE
                    log.info('value of %r=%r -> throttle %s best-effort tasks', 
                             self.metric_name, value, len(be_tasks))
                    self._steady_duration = 10
                else:
                    self._steady_duration -= 1
                    # Enable only if steady state for at least 5 rounds.
                    if self._steady_duration == 0:
                        allocation = ENABLE
                        log.info('value of %r=%r -> enable %s best-effort tasks', 
                                 self.metric_name, value, len(be_tasks))
                        self._steady_duration = 10
                    else:
                        allocation = THROTTLE

                new_allocations = {t: allocation for t in be_tasks}

        # Return additional metrics to debug internals of example allocator.
        return new_allocations, anomalies, [
            Metric(name='example_allocator_value', value=value,
                   labels=dict(kind='current')),
            Metric(name='example_allocator_value', value=self.threshold,
                   labels=dict(kind='threshold')),
        ]
