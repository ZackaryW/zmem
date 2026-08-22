class MetaExpander:
    extension_id = "META"

    def expand(self, context) -> None:
        context.metadata_patch(context.annotation.patch)
