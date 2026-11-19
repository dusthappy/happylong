<!doctype html>
<html lang="$lang">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
  <title>$title · happlylong</title>
  <style>
    :root {
      color-scheme: light;
      --paper: #f5f7f6;
      --white: #fff;
      --ink: #192e2a;
      --muted: #50645d;
      --line: #d5dfda;
      --deep: #11392f;
      --focus: #08735a;
      --wash: #edf4ef;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
      line-height: 1.5;
    }
    *, *::before, *::after { box-sizing: border-box; }
    [hidden] { display: none !important; }
    body { margin: 0; color: var(--ink); background: var(--paper); }
    a { color: inherit; }
    button, input, select { font: inherit; color: inherit; }
    :focus-visible { outline: 2px solid var(--focus); outline-offset: 3px; }
    ::selection { color: #11372e; background: #bcebd6; }
    code { font-family: ui-monospace, "SFMono-Regular", Consolas, monospace; overflow-wrap: anywhere; }
    h1, h2, h3, p { margin: 0; }

    .wrap { width: min(100% - 2rem, 87rem); margin-inline: auto; }
    .masthead { color: #f3fcf7; background: var(--deep); padding-block: 1.5rem; }
    .masthead .wrap { display: flex; flex-wrap: wrap; align-items: end; justify-content: space-between; gap: .5rem 2rem; }
    .masthead h1 { font-size: 1.85rem; letter-spacing: -.03em; }
    .snapshot { color: #cee5d8; font-size: .83rem; }
    time, .totals dd, .directory small { font-variant-numeric: tabular-nums; }

    .totals { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: 0; border-bottom: 1px solid var(--line); }
    .totals > div { display: flex; align-items: baseline; gap: .5rem; padding: .6rem .7rem; }
    .totals dt { font-size: .84rem; color: var(--muted); }
    .totals dd { order: -1; margin: 0; font-weight: 750; font-size: 1.25rem; }

    .workspace { display: grid; align-items: start; gap: 1.3rem; padding-block: 1.25rem 2rem; }
    .content { min-width: 0; }
    .directory { min-width: 0; }
    .directory summary { min-height: 2.75rem; padding: .65rem .5rem; font-size: .91rem; font-weight: 650; cursor: pointer; }
    .directory ul { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 9rem), 1fr)); gap: .2rem; margin: 0; padding: 0; list-style: none; }
    .directory a { display: flex; min-height: 2.75rem; align-items: center; justify-content: space-between; gap: .5rem; padding: .4rem .5rem; border-radius: .35rem; text-decoration: none; font-size: .84rem; }
    .directory a:hover { background: #e6efe9; }
    .directory span { min-width: 0; overflow-wrap: anywhere; }
    .directory small { color: var(--muted); font-size: .76rem; }

    .filters { display: flex; flex-wrap: wrap; align-items: end; gap: .6rem; margin-bottom: .95rem; }
    .filters label { display: grid; min-width: 0; gap: .2rem; color: var(--muted); font-size: .82rem; }
    .filters label:first-child { flex: 1 1 18rem; }
    .filters label:nth-child(2) { flex: 0 1 auto; max-width: 100%; }
    .filters input, .filters select, .filters button {
      min-width: 0; min-height: 2.75rem; border: 1px solid #9eafa6; border-radius: .35rem; background: var(--white);
      padding: .45rem .65rem; color: var(--ink); font-size: .9rem;
    }
    .filters input::placeholder { color: var(--muted); }
    .filters button { cursor: pointer; }
    .filters button:hover:not(:disabled) { background: var(--wash); }
    .filters button:disabled { color: var(--muted); background: transparent; border-color: var(--line); cursor: default; }
    .result-count { margin-bottom: .8rem; color: var(--muted); font-size: .85rem; }
    .result-count:empty { display: none; }

    .project { background: var(--white); border: 1px solid var(--line); border-radius: .7rem; margin-bottom: 1rem; scroll-margin-top: 1rem; }
    .project:target { border-color: var(--focus); }
    .project > header { display: flex; flex-wrap: wrap; align-items: baseline; gap: .1rem .75rem; padding: .85rem 1rem .65rem; }
    .project > header h2 { font-size: 1.17rem; overflow-wrap: anywhere; }
    .project > header code { color: var(--muted); font-size: .76rem; }
    .repo-grid { display: grid; gap: .85rem 1.25rem; padding: .1rem 1rem 1rem; }
    .repo-grid h3 { margin-bottom: .25rem; color: var(--muted); font-size: .78rem; }
    .repo-grid ul { display: grid; gap: .55rem; margin: 0; padding: 0; list-style: none; }
    .repo-grid li { min-width: 0; line-height: 1.45; }
    .repo-grid code { font-size: .85rem; font-weight: 650; }
    .repo-grid li p { margin-top: .22rem; color: var(--muted); font-size: .79rem; overflow-wrap: anywhere; }
    .repo-tag { display: inline-block; margin-inline-start: .35rem; color: #315c4c; font-size: .72rem; }
    .repo-paths { display: grid; gap: .3rem; margin: .45rem 0; }
    .repo-paths > div { display: grid; grid-template-columns: 7rem minmax(0, 1fr); align-items: baseline; gap: .4rem; }
    .repo-paths dt { color: var(--muted); font-size: .78rem; }
    .repo-paths dd { display: flex; flex-wrap: wrap; gap: .25rem .35rem; margin: 0; color: var(--muted); font-size: .78rem; }
    .repo-paths code { max-width: 100%; color: var(--ink); background: var(--wash); padding: .06rem .35rem; border-radius: .25rem; font-size: .79rem; }
    :lang(zh) .repo-paths > div { grid-template-columns: 3.6rem minmax(0, 1fr); }
    .note { color: var(--muted); font-size: .88rem; }
    .project > .note { padding: .5rem 1rem 1rem; }
    .table-hint { color: var(--muted); font-size: .76rem; margin: 0 1rem .35rem; }
    .table-scroll { overflow-x: auto; border-radius: 0 0 .65rem .65rem; }
    .table-scroll:focus-visible { outline-offset: -2px; }
    table { width: 100%; min-width: 39rem; border-spacing: 0; text-align: start; font-size: .83rem; }
    thead { background: var(--wash); color: #37584c; }
    th, td { text-align: start; vertical-align: top; padding: .48rem .45rem; }
    :is(th, td):first-child { padding-inline-start: 1rem; width: 42%; }
    :is(th, td):last-child { padding-inline-end: 1rem; }
    tbody tr + tr > * { border-top: 1px solid #e7eeea; }
    tbody tr:hover { background: #fafcfb; }
    tbody th strong { display: block; font-weight: 600; overflow-wrap: anywhere; }
    tbody th code { display: block; font-size: .72rem; font-weight: 400; color: var(--muted); }
    .badge { display: inline-block; max-width: 10rem; padding: .13rem .48rem; border-radius: .3rem; font-size: .75rem; font-weight: 600; overflow-wrap: anywhere; }
    .badge.neutral { color: #4e6057; background: #eef1ef; }
    .badge.active { color: #224c77; background: #e8f0fb; }
    .badge.success { color: #155b43; background: #e2f2e9; }
    .badge.danger { color: #8b3028; background: #faeae6; }

    .notices { padding: .65rem .9rem; margin-bottom: .9rem; border: 1px solid #e2d3b5; border-radius: .4rem; background: #fff8e9; color: #614921; font-size: .87rem; overflow-wrap: anywhere; }
    .notices summary { cursor: pointer; font-weight: 650; }
    .notices ul { padding-inline-start: 1.2rem; margin-bottom: 0; }
    .footer { border-top: 1px solid var(--line); padding-block: .85rem 1.35rem; color: var(--muted); font-size: .82rem; }
    .footer code { color: var(--ink); }

    @media (min-width: 34rem) {
      .totals { display: flex; }
      .totals > div { padding-inline: 1rem; border-inline-end: 1px solid var(--line); }
    }
    @media (min-width: 43rem) {
      .repo-grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 11rem), 1fr)); }
      .table-hint { display: none; }
    }
    @media (min-width: 63rem) {
      .wrap { width: min(100% - 4rem, 87rem); }
      .workspace { grid-template-columns: 14rem minmax(0, 1fr); gap: 1.5rem; }
      .directory { position: sticky; top: 1rem; max-height: calc(100vh - 2rem); overflow: auto; padding: .25rem; }
      .directory ul { display: block; }
    }
  </style>
</head>
<body>
  <header class="masthead">
    <div class="wrap">
      <h1>$title</h1>
      <p class="snapshot">$updated <time datetime="$generated_at">$generated_label</time></p>
    </div>
  </header>
  <div class="wrap">
    <dl class="totals">
      <div><dt>$projects_label</dt><dd>$project_count</dd></div>
      <div><dt>$iterations_label</dt><dd>$iteration_count</dd></div>
      <div><dt>$open_label</dt><dd>$open_count</dd></div>
      <div><dt>$done_label</dt><dd>$done_count</dd></div>
    </dl>
    <div class="workspace">
      <nav class="directory" aria-labelledby="directory-title">
        <details id="project-directory" open>
          <summary id="directory-title">$navigation</summary>
          <ul>$project_links</ul>
        </details>
      </nav>
      <main class="content">
        $notices_markup
        <div class="filters" id="filters" hidden>
          <label>$search <input id="search" type="search" placeholder="$search_hint"></label>
          <label>$status <select id="status"><option value="">$all_statuses</option>$status_options</select></label>
          <button id="reset" type="button" disabled>$reset</button>
        </div>
        <p class="result-count" id="result-count" role="status"
           data-projects="$projects_label" data-iterations="$iterations_label"></p>
        <p id="no-results" class="note" hidden>$no_results</p>
        $project_sections
      </main>
    </div>
    <footer class="footer">$refresh · <code>python3 happlylong.py dashboard</code></footer>
  </div>
  <script>
    (() => {
      const entries = Array.from(document.querySelectorAll(".directory li"), (item) => {
        const project = document.getElementById(item.querySelector("a").hash.slice(1));
        const text = Array.from(project.querySelectorAll("header, .repo-grid"))
          .map((element) => element.textContent).join(" ").toLowerCase();
        const rows = Array.from(project.querySelectorAll("tbody tr"), (row) => ({
          row,
          text: row.querySelector("th").textContent.toLowerCase(),
          status: "status:" + row.querySelector(".overall .badge").dataset.value,
        }));
        return { item, project, text, rows };
      });
      if (!entries.length) return;
      if (window.matchMedia("(max-width: 42.99rem)").matches) {
        document.getElementById("project-directory").open = false;
      }

      const search = document.getElementById("search");
      const status = document.getElementById("status");
      const reset = document.getElementById("reset");
      const result = document.getElementById("result-count");
      const empty = document.getElementById("no-results");
      function filter() {
        const query = search.value.trim().toLowerCase();
        const state = status.value;
        const filtering = Boolean(query || state);
        let projects = 0;
        let iterations = 0;
        for (const { item, project, text, rows } of entries) {
          const matchesProject = text.includes(query);
          let visibleRows = 0;
          for (const entry of rows) {
            const matchesText = matchesProject || entry.text.includes(query);
            const matchesStatus = !state || state === entry.status;
            entry.row.hidden = !(matchesText && matchesStatus);
            if (!entry.row.hidden) visibleRows++;
          }
          const visible = rows.length ? visibleRows > 0 : matchesProject && !state;
          item.hidden = !visible;
          project.hidden = !visible;
          item.querySelector("small").textContent = visibleRows;
          if (visible) projects++;
          iterations += visibleRows;
        }
        reset.disabled = !filtering;
        empty.hidden = projects > 0;
        result.textContent = filtering
          ? result.dataset.projects + " " + projects + " · " + result.dataset.iterations + " " + iterations
          : "";
      }

      search.addEventListener("input", filter);
      status.addEventListener("change", filter);
      reset.addEventListener("click", () => {
        search.value = "";
        status.value = "";
        search.focus();
        filter();
      });
      document.getElementById("filters").hidden = false;
      filter();
    })();
  </script>
</body>
</html>
