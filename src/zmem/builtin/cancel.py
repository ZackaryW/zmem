class CancelExpander:
    extension_id = "CANCEL"

    def expand(self, context) -> None:
        context.cancel(context.annotation.target)
