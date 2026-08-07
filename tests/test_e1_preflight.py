from __future__ import annotations

import socket
import unittest

from experiments.e1_capacity_bottleneck.preflight import PreflightError, ensure_port_available


class PortPreflightTests(unittest.TestCase):
    def test_free_port_is_accepted(self) -> None:
        with socket.socket() as holder:
            holder.bind(("127.0.0.1", 0))
            port = holder.getsockname()[1]
        ensure_port_available(port)

    def test_bound_port_is_rejected(self) -> None:
        with socket.socket() as holder:
            holder.bind(("127.0.0.1", 0))
            with self.assertRaises(PreflightError):
                ensure_port_available(holder.getsockname()[1])


if __name__ == "__main__":
    unittest.main()
