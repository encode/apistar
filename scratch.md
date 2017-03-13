class MyPlugin:
    def pytest_collection_modifyitems(self, items, config):
        for item in items:
            if item.name == 'test_abc':
                # print(item)
                # print(item.name)
                # print(dir(item))
                p = pytest.mark.parametrize('foo', ['directly-overridden-username'])
                item.add_marker(p)
                print(list(item.keywords))

plugins=[MyPlugin()]

gunicorn app:app.wsgi --workers=2 --bind=0.0.0.0:5000 --pid=pid --worker-class=meinheld.gmeinheld.MeinheldWorker

# Processors, Services, Functions, Operations, Mappings, Resolvers, Directives, Plugins, Components

Header, QueryParam
Werkzeug routing, PathComponent, Path, RelativePath
