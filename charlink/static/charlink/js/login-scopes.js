(() => {
    const apps = Array.from(document.querySelectorAll('[data-charlink-app]'), (el) => ({
        el,
        id: el.dataset.charlinkApp,
        checkbox: el.querySelector('input[type="checkbox"]'),
    }));
    const scopes = Array.from(document.querySelectorAll('[data-charlink-scope]'), (el) => ({
        el,
        appIds: el.dataset.charlinkApps.split(' '),
    }));

    let hoveredApp = null;
    let hoveredScope = null;

    const render = () => {
        const checked = new Set(apps.filter((app) => app.checkbox.checked).map((app) => app.id));

        scopes.forEach((scope) => {
            const inList = scope.appIds.some((id) => checked.has(id));
            const hovered = scope.appIds.includes(hoveredApp);
            scope.el.classList.toggle('d-none', !inList && !hovered);
            scope.el.classList.toggle('text-bg-info', hovered && inList);
            scope.el.classList.toggle('text-bg-success', hovered && !inList);
            scope.el.classList.toggle('text-bg-secondary', !hovered);
        });

        apps.forEach((app) => {
            app.el.classList.toggle('text-info', hoveredScope !== null && hoveredScope.appIds.includes(app.id));
        });
    };

    apps.forEach((app) => {
        app.checkbox.addEventListener('change', render);
        app.el.addEventListener('mouseenter', () => { hoveredApp = app.id; render(); });
        app.el.addEventListener('mouseleave', () => { hoveredApp = null; render(); });
    });

    scopes.forEach((scope) => {
        scope.el.addEventListener('mouseenter', () => { hoveredScope = scope; render(); });
        scope.el.addEventListener('mouseleave', () => { hoveredScope = null; render(); });
    });

    render();
})();
