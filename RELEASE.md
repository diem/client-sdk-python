
# Release a new version

* Update setup.py, bump up version
* Commit and merge

```
git checkout <releasse version>
git tag vX.X.X
git push origin --tags
```

# Update docs:

* checkout gh-pages branch
* ```make docs``` to update docs
* revert changes to docs/index.md and docs/_config.yaml (need fix pdoc to not delete them or generate them)
* commit the change and push to gh-pages
