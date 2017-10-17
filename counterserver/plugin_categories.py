from yapsy.IPlugin import IPlugin


class IEventReceiverPlugin(IPlugin):
    """
    The interface that must be implemented in plugins that needs to be notified
    when the server receives or generates an event.
    """
    def on_event(self, event_time, event_type, event_image=None, node_id=None):
        """
        Called when the server receives or generates an event. A dictionary
        can be returned to enrich the event with additional information.
        """
        raise NotImplementedError
