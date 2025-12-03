class EventBus:
    def __init__(self):
        self._subs = {}

    def subscribe(self, name, callback):
        if name not in self._subs:
            self._subs[name] = []
        self._subs[name].append(callback)

    def publish(self, name, data=None):
        if name in self._subs:
            for cb in self._subs[name]:
                cb(data)

event_bus = EventBus()
