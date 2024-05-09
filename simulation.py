from dataclasses import dataclass
from enum import StrEnum
from heapq import heappop, heappush, heapify
from math import log
from random import random


class EventType(StrEnum):
    ARRIVE = 'packet_arrival'
    TRANSMIT = 'packet_transmit'
    RECEIVE = 'packet_received'
    ACK = 'packet_ack'
    TIMEOUT = 'packet_timeout'


@dataclass(order=True)
class Packet:
    seq: int
    time: float
    sent: bool = False
    acked: bool = False


@dataclass(order=True)
class Event:
    time: float
    event_type: EventType
    seq: int


class ARQMode(StrEnum):
    GO_BACK_N = 'go_back_n'
    SELECTIVE_REPEAT = 'selective_repeat'


class Simulation:
    last_event: Event

    def __init__(
        self,
        trace: bool = False,
        mode: ARQMode = ARQMode.GO_BACK_N,
        sim_max: int = 1000, window: int = 1,
        arrival_rate: float = 1,
        fwd_err_rate: float = 0.0, bwd_err_rate: float = 0.0,
        trans_time: float = 1,
        prop_ratio: float = 1, timeout_ratio: float = 2,
    ) -> None:
        self.trace = trace
        self.mode = mode

        self.sim_max = sim_max

        self.window = window
        self.arrival_rate = arrival_rate
        self.fwd_err_rate = fwd_err_rate
        self.bwd_err_rate = bwd_err_rate
        self.trans_time = trans_time
        self.prop_ratio = prop_ratio
        self.timeout_ratio = timeout_ratio

        # various queues
        self.event_queue: list[Event] = []
        self.wait_queue: list[int] = []
        self.trans_queue: list[int] = []

        # packet lookup
        self.packets: list[Packet] = []

        # sender state
        self.trans_ready = True

        # receiver state
        self.recv_count = 0
        # for selective repeat
        self.recv_buf: list[int] = []

        # metrics
        self.delay_sum = 0.0
        self.trans_count = 0

    def run(self) -> tuple[float, float]:
        first_packet = Packet(0, self.arrival_delay())
        self.packets.append(first_packet)
        heappush(self.event_queue, Event(first_packet.time, EventType.ARRIVE, 0))

        while self.recv_count < self.sim_max:
            self.step()

        return self.stats()

    def step(self) -> None:
        ev = heappop(self.event_queue)
        self.last_event = ev

        if self.trace:
            print(ev)

        self.handle_event(ev)
        self.send_packet(ev)

    def arrival_delay(self) -> float:
        return -log(random()) / self.arrival_rate

    def prop_delay(self) -> float:
        return self.trans_time * (1 + self.prop_ratio)

    def timeout_delay(self) -> float:
        return self.prop_delay() * self.timeout_ratio

    def stats(self) -> tuple[float, float]:
        delay = self.delay_sum / self.recv_count
        util = self.trans_count * self.trans_time / self.last_event.time
        return delay, util

    def handle_event(self, ev: Event) -> None:
        match ev.event_type:
            case EventType.ARRIVE:
                # new packet arrived, add to wait queue
                heappush(self.wait_queue, ev.seq)

                if ev.seq + 1 < self.sim_max:
                    # add next arrival to event queue
                    next_packet = Packet(ev.seq + 1, ev.time + self.arrival_delay())
                    self.packets.append(next_packet)
                    heappush(self.event_queue, Event(next_packet.time, EventType.ARRIVE, next_packet.seq))

            case EventType.TRANSMIT:
                # previous packet has been fully transmitted, ready for next transmit
                self.trans_ready = True
                self.trans_count += 1

            case EventType.RECEIVE:
                if random() < self.fwd_err_rate:
                    # packet error, ignore
                    return

                if ev.seq < self.recv_count:
                    # duplicate arrival, resend ack
                    heappush(self.event_queue, Event(ev.time + self.prop_delay() - self.trans_time, EventType.ACK, self.recv_count - 1))
                    return

                # packet received
                if self.mode == ARQMode.GO_BACK_N:
                    if ev.seq == self.recv_count:
                        # packet arrived, emit ack
                        heappush(self.event_queue, Event(ev.time + self.prop_delay() - self.trans_time, EventType.ACK, ev.seq))
                        self.recv_count += 1
                        self.delay_sum += ev.time - self.packets[ev.seq].time
                else:
                    if ev.seq in self.recv_buf:
                        # duplicate unacked packet, resend ack
                        heappush(self.event_queue, Event(ev.time + self.prop_delay() - self.trans_time, EventType.ACK, self.recv_count - 1))
                        return

                    heappush(self.recv_buf, ev.seq)
                    while self.recv_buf and self.recv_buf[0] == self.recv_count:
                        # packet arrived
                        seq = heappop(self.recv_buf)
                        self.recv_count += 1
                        self.delay_sum += ev.time - self.packets[seq].time

                    # emit max ack
                    heappush(self.event_queue, Event(ev.time + self.prop_delay() - self.trans_time, EventType.ACK, self.recv_count - 1))

            case EventType.ACK:
                if random() < self.bwd_err_rate:
                    # ack error, ignore
                    return

                # ack received, open window
                while self.trans_queue and ev.seq >= self.trans_queue[0]:
                    seq = heappop(self.trans_queue)
                    # ensure no retransmissions
                    self.packets[seq].acked = True

            case EventType.TIMEOUT:
                if self.mode == ARQMode.GO_BACK_N:
                    if ev.seq not in self.trans_queue:
                        # unknown packet, ignore
                        return

                    # retransmit all packets in fwd window
                    for seq in self.trans_queue:
                        if seq >= ev.seq:
                            heappush(self.wait_queue, seq)
                    # remove timeouts for queued retransmissions
                    self.event_queue = [e for e in self.event_queue if e.event_type != EventType.TIMEOUT or e.seq < ev.seq]
                    heapify(self.event_queue)

                else:
                    if ev.seq not in self.trans_queue:
                        # unknown packet, ignore
                        return

                    # retransmit packet
                    heappush(self.wait_queue, ev.seq)

    def send_packet(self, ev: Event) -> None:
        while self.trans_ready and self.wait_queue:
            seq = heappop(self.wait_queue)

            if self.packets[seq].acked:
                # packet has been acked since it was re-queued, choose next packet
                continue

            if not self.packets[seq].sent:
                if self.window - len(self.trans_queue) == 0:
                    # window is full, wait for ack
                    heappush(self.wait_queue, seq)
                    return
                # first transmission, add to transmission queue
                self.packets[seq].sent = True
                heappush(self.trans_queue, seq)

            # mark as busy
            self.trans_ready = False
            heappush(self.event_queue, Event(ev.time + self.trans_time, EventType.TRANSMIT, seq))

            # send packet
            heappush(self.event_queue, Event(ev.time + self.prop_delay(), EventType.RECEIVE, seq))
            heappush(self.event_queue, Event(ev.time + self.timeout_delay(), EventType.TIMEOUT, seq))
