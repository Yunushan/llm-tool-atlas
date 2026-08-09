PYTHON ?= python3

.PHONY: check render test validate release-check release audit-links freshness

check:
	$(PYTHON) scripts/verify.py

render:
	$(PYTHON) scripts/render_catalog.py

test:
	$(PYTHON) -m unittest discover -s tests -v

validate:
	$(PYTHON) scripts/validate_catalog.py

release-check:
	$(PYTHON) scripts/check_release.py

release:
	$(PYTHON) scripts/build_release.py

audit-links:
	$(PYTHON) scripts/audit_links.py --timeout 15 --workers 12 --retries 2

freshness:
	$(PYTHON) scripts/verify.py --max-age-days 90
