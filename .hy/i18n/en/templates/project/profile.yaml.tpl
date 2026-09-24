schema: 1
project: $project
title: $title
description: $description
created: $created
updated: $created

# Tech stack (hand-maintained; doctor warns on detection drift)
stack:
  langs: []
  frameworks: []

# Codebase registry (maintained by happlylong.py link add)
# Fields: role(frontend|backend|service|fullstack|lib) / target(absolute path) / langs /
#         desc(one-line functional role) / shared(cross-project shared repo) /
#         backend_apps(shared-repo subprojects) / pending(target not ready) / note
# Active iterations are not stored in the project profile; each agent session has its own binding under .hy/session/bindings/.
repos: {}
