# CI

> [!WARNING]
> CI is constantly evolving, this study may easily disagree
> with the latest CIs in repository. Feel free to modify or
> improve this document as you use the CI and notice
> anything odd, much appreciated!

The CIs of Kata Containers relies on [GitHub Actions][gh-actions] to get them to work. Since these CIs should be triggered each time the observed branches are pushed, `GitHub actions` are the natural way to do it.

## Kata Containers' GitHub Actions

CIs in Kata Containers needs helper scripts to get ready for performing actually tests. These helper scripts are generally preparing, setting up the environment necessary (and etc.) for logic in CI scripts.

### Workflows

Kata Containers' CIs are not all triggered when specific branches are pushed. It could be categorized into two classes:

- Jobs run automatically when a PR is raised (or updated, force-pushed, etc.)
- Jobs requires maintainers' approval to run

#### Jobs run automatically when a PR is raised

These jobs are designed to ensure:

- The commit message is in the expected format
- The Developer's Certificate of Origin is present
- Static checks are passing

Simply put, these jobs are generally light-weight, trivial (relate to massive building jobs) which could be placed on "cost free" runners (provided by GitHub Actions for example). This phase is trying to evaluate that the PR may be ready for reviewing.

#### Jobs requires maintainers' approval to run

These jobs are the actual "CI"s, including:

- on "cost free", or bare-metal depending on architectures
  - Building tests of all components
  - Creating tarball with all components
  - Kata Containers specific...
- on bare-metal
  - Metrics
- on Azure instances
  - Kata Containers specific...

They require a maintainer's approval to run, and parts of those jobs will be running on "paid" runners. As of Kata Containers, it uses Azure infrastructure.

Or if the PR is given a "green light" (by adding an `ok-to-test` label to the PR), these tests could now be triggered by commenting `/test` as part of a PR review.

For all the tests relying on Azure instances of Kata Containers' case (on "paid" runners), real money is being spent, so Kata Containers community asks the maintainers to be mindful about those, hence avoid abusing them to merely debug issues.
