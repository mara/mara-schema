Design Decisions
================

Schema sync to front-ends
-------------------------
When reporting tools have a Metadata API (e.g. Metabase, Tableau) or can read schema definitions from text files (e.g. Looker, Mondrian), then it's easy to sync definitions with them. The `Mara Metabase <https://github.com/mara/mara-metabase>`_ package contains a function for syncing Mara Schema definitions with Metabase and the `Mara Mondrian <https://github.com/mara/mara-mondrian>`_ package contains a generator for a Mondrian schema.

We welcome contributions for creating Looker `LookML files <https://docs.looker.com/data-modeling/getting-started/file-types-in-project>`_, for syncing definitions with Tableau, and for syncing with any other BI front-end.

Also, we see a potential for automatically creating data guides in other Wikis or documentation tools.
