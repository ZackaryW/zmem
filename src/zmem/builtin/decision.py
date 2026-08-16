class DecisionExpander:
    extension_id = "DECISION"

    def expand(self, context) -> None:
        context.add_entry(type=self.extension_id, content=context.annotation.content)
