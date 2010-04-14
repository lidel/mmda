from mmda.engine.utils import mmda_logger


class CachedDocument:
    """
    Template for CachedDocuments.
    """

    # would be nice to  put 'cache_state' here,
    # but couchdbkit architecture makes it tricky atm
    # (place for future improvements)

    def save_any_changes(self):
        """
        Store document in the database if it is marked as 'changes_present'.
        """
        if 'changes_present' in self:
            del self.changes_present
            self.save()
            mmda_logger('db','store',self)

