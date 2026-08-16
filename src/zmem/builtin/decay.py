class DecayExpander:
    extension_id = "DECAY"

    def expand(self, context) -> None:
        context.decay(context.annotation.target, factor=context.annotation.factor)
