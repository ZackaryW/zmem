class LessonLearntExpander:
    extension_id = "LESSON_LEARNT"

    def expand(self, context) -> None:
        context.add_entry(type=self.extension_id, content=context.annotation.content)
