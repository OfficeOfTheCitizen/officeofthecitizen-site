document.querySelectorAll("[data-menu]").forEach((menu) => {
  const button = menu.querySelector(".menu-button");
  const panel = menu.querySelector(".menu-panel");
  if (!button || !panel) return;
  panel.hidden = true;
  const setOpen = (open) => {
    menu.classList.toggle("is-open", open);
    button.setAttribute("aria-expanded", open ? "true" : "false");
    panel.hidden = !open;
  };
  button.addEventListener("pointerdown", (event) => {
    event.stopPropagation();
  });
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    setOpen(!menu.classList.contains("is-open"));
  });
  panel.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => setOpen(false));
  });
  document.addEventListener("pointerdown", (event) => {
    if (!menu.contains(event.target)) setOpen(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setOpen(false);
  });
});

(() => {
  const scroller = document.querySelector(".page-scroll");
  const links = Array.from(document.querySelectorAll(".toc-list a"));
  const progress = document.getElementById("progressBar");
  if (!scroller || !links.length || !progress) return;

  const targets = links
    .map((a) => document.querySelector(a.getAttribute("href")))
    .filter(Boolean);

  const tocMap = new Map(links.map((a) => [a.getAttribute("href").slice(1), a]));
  const paneMode = () => window.matchMedia("(min-width: 1061px)").matches;
  const getTop = (el) => paneMode()
    ? el.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop
    : el.getBoundingClientRect().top + window.scrollY;

  const setActive = (id) => {
    links.forEach((a) => a.classList.remove("active"));
    const link = tocMap.get(id);
    if (link) link.classList.add("active");
  };

  const updateActive = () => {
    const anchor = paneMode()
      ? scroller.scrollTop + Math.max(120, scroller.clientHeight * 0.2)
      : window.scrollY + Math.max(120, window.innerHeight * 0.22);
    let current = targets[0];
    for (const el of targets) {
      const top = getTop(el);
      if (top <= anchor) current = el;
      else break;
    }
    if (current) setActive(current.id);
  };

  const updateProgress = () => {
    const max = paneMode()
      ? scroller.scrollHeight - scroller.clientHeight
      : document.documentElement.scrollHeight - window.innerHeight;
    const current = paneMode() ? scroller.scrollTop : window.scrollY;
    const pct = max > 0 ? (current / max) * 100 : 0;
    progress.style.width = Math.min(100, Math.max(0, pct)) + "%";
  };

  let raf = 0;
  const schedule = () => {
    if (raf) return;
    raf = window.requestAnimationFrame(() => {
      raf = 0;
      updateActive();
      updateProgress();
    });
  };

  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener("click", (event) => {
      const target = document.querySelector(link.getAttribute("href"));
      if (!target) return;
      if (paneMode()) {
        event.preventDefault();
        scroller.scrollTo({ top: Math.max(0, getTop(target) - 18), behavior: "smooth" });
        if (history.pushState) history.pushState(null, "", link.getAttribute("href"));
      }
    });
  });

  if (paneMode()) scroller.addEventListener("scroll", schedule, { passive: true });
  else window.addEventListener("scroll", schedule, { passive: true });

  window.addEventListener("resize", () => {
    if (paneMode()) {
      scroller.addEventListener("scroll", schedule, { passive: true });
      window.removeEventListener("scroll", schedule);
    } else {
      window.addEventListener("scroll", schedule, { passive: true });
      scroller.removeEventListener("scroll", schedule);
    }
    schedule();
  });

  schedule();
})();
