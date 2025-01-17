from indra.java_vm import autoclass, JavaException

class ReachReader(object):
    """The ReachReaader wraps a singleton instance of the REACH reader.

    This allows calling the reader many times without having to wait for it to
    start up each time.

    Attributes
    ----------
    api_ruler : edu.arizona.sista.reach.apis.ApiRuler
        An instance of the REACH ApiRuler class (java object).
    """
    def __init__(self):
        self.api_ruler = None

    def get_api_ruler(self):
        """Return the existing reader if it exists or launch a new one.

        Returns
        -------
        api_ruler : edu.arizona.sista.reach.apis.ApiRuler
            An instance of the REACH ApiRuler class (java object).
        """
        if self.api_ruler is None:
            try:
                self.api_ruler =\
                    autoclass('edu.arizona.sista.reach.apis.ApiRuler')
            except JavaException:
                try:
                    autoclass('java.lang.String')
                except JavaException:
                    pass
                return None
        return self.api_ruler
