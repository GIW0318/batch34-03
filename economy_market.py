class OrderBook:
    def __init__(self):
        self._orders = {}
        self._trades = []
        self._seq = 0

    def submit(self, order_id, side, price, qty, now):
        if order_id in self._orders:
            raise ValueError(f"duplicate order id: {order_id!r}")
        if side not in ("buy", "sell"):
            raise ValueError(f"invalid side: {side!r}")
        if not self._is_positive_int(price):
            raise ValueError("price must be a positive integer")
        if not self._is_positive_int(qty):
            raise ValueError("qty must be a positive integer")
        if not self._is_non_negative_int(now):
            raise ValueError("now must be a non-negative integer")
        self._orders[order_id] = {
            "id": order_id,
            "side": side,
            "price": price,
            "qty": qty,
            "time": now,
            "seq": self._seq,
        }
        self._seq += 1
        return None

    @staticmethod
    def _is_positive_int(value):
        return isinstance(value, int) and not isinstance(value, bool) and value > 0

    @staticmethod
    def _is_non_negative_int(value):
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0

    def match(self):
        new_trades = []
        while True:
            best_bid = self._best_order("buy")
            best_ask = self._best_order("sell")
            if best_bid is None or best_ask is None:
                break
            if best_bid["price"] < best_ask["price"]:
                break
            trade_qty = min(best_bid["qty"], best_ask["qty"])
            if (best_bid["time"], best_bid["seq"]) <= (
                best_ask["time"],
                best_ask["seq"],
            ):
                trade_price = best_bid["price"]
            else:
                trade_price = best_ask["price"]
            trade = {
                "buy": best_bid["id"],
                "sell": best_ask["id"],
                "price": trade_price,
                "qty": trade_qty,
            }
            self._trades.append(trade)
            new_trades.append(trade)
            best_bid["qty"] -= trade_qty
            best_ask["qty"] -= trade_qty
            if best_bid["qty"] == 0:
                del self._orders[best_bid["id"]]
            if best_ask["qty"] == 0:
                del self._orders[best_ask["id"]]
        return [dict(trade) for trade in new_trades]

    def _best_order(self, side):
        candidates = [order for order in self._orders.values() if order["side"] == side]
        if not candidates:
            return None
        if side == "buy":
            return min(
                candidates,
                key=lambda order: (-order["price"], order["time"], order["seq"]),
            )
        return min(
            candidates,
            key=lambda order: (order["price"], order["time"], order["seq"]),
        )

    def cancel(self, order_id):
        if order_id not in self._orders:
            raise ValueError(f"unknown or inactive order id: {order_id!r}")
        del self._orders[order_id]
        return None

    def book(self):
        return {
            "bids": self._side_snapshot("buy"),
            "asks": self._side_snapshot("sell"),
        }

    def _side_snapshot(self, side):
        orders = [order for order in self._orders.values() if order["side"] == side]
        if side == "buy":
            orders.sort(key=lambda order: (-order["price"], order["time"], order["seq"]))
        else:
            orders.sort(key=lambda order: (order["price"], order["time"], order["seq"]))
        return [
            {"id": order["id"], "price": order["price"], "qty": order["qty"]}
            for order in orders
        ]

    def trades(self):
        return [dict(trade) for trade in self._trades]

    def state(self):
        snapshot = self.book()
        snapshot["trades"] = self.trades()
        return snapshot
