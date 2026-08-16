# Extension API

## Expander Contract

An expander exposes a stable uppercase `extension_id` and an `expand(context) -> None` method. The context contains the parsed `annotation`, read-only commit metadata (`sha`, `commit_time`, and `scope`), and the resolved repository path.

Use only these canonical actions:

- `context.add_entry(type, content, score=1.0)`
- `context.add_relationship(source, target, score=1.0)`
- `context.decay(target, factor)`
- `context.cancel(target)`
- `context.diagnose(message)`

Scores and decay factors must be finite values from `0.0` through `1.0`. Actions are journaled for the service; do not update SQLite directly and do not return a mapping.

```python
API_VERSION = 1


class RiskExpander:
    extension_id = "RISK"

    def expand(self, context) -> None:
        context.add_entry(
            type=self.extension_id,
            content=context.annotation.content,
            score=1.0,
        )


def register(registry, mode="extend") -> None:
    expander = RiskExpander()
    if mode == "overwrite":
        registry.overwrite(expander.extension_id, expander)
    else:
        registry.extend(expander.extension_id, expander)
```

`extend` requires a new ID. `overwrite` requires an existing target, and duplicate overwrite attempts fail. A custom plain annotation materializes only when its expander is registered.

## Hook Contract

Hooks register for `after_expand` or `after_index`. A callback receives copied context and must return `None`. A non-`None` return is rejected; callback exceptions are isolated as diagnostics and do not erase accepted entries.

```python
API_VERSION = 1


def audit(context) -> None:
    # Observe or perform a bounded external action. Do not mutate canonical results.
    return None


def register(registry) -> None:
    registry.register("after_index", audit)
```

If behavior must create or alter entries, relationships, scores, validity, or diagnostics, implement an expander instead of a hook.

## Discovery and Layering

Global modules are importable Python files under:

```text
~/.zmem/ext/expanders/*.py
~/.zmem/ext/hooks/*.py
```

Repository modules use `${ZMEM_CUSTOM_EXT_ROOT:-.zmem}`:

```text
<root>/extend/expanders/*.py
<root>/extend/hooks/*.py
<root>/overwrite/expanders/*.py
<root>/overwrite/hooks/*.py
```

Repository extensions execute only for a repository added with extension trust, such as `zmem-svc add <path> --trust-extensions`. Treat trust as code-execution authority, not as a parser option.

Every module must expose `API_VERSION = 1` and callable `register`. Files are discovered recursively in deterministic case-insensitive path order. Source or path changes alter extension identity and trigger rebuilding; do not depend on incidental filesystem order.

Keep reusable framework abstractions under `src/zmem/ext/expander/` or `src/zmem/ext/hooks/`, utility code under `src/zmem/utils/`, and built-in implementations under `src/zmem/builtin/`.
