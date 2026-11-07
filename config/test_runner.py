from django.test.runner import DiscoverRunner


class AppsDiscoverRunner(DiscoverRunner):
    """Custom test runner that defaults to discovering tests in the `apps` package."""

    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            test_labels = ['apps']
        return super().build_suite(test_labels=test_labels, **kwargs)

