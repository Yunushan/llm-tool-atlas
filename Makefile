.PHONY: check render test validate audit-links

check: validate test
	python3 scripts/render_catalog.py --check
	python3 scripts/check_local_links.py

render:
	python3 scripts/render_catalog.py

test:
	python3 -m unittest discover -s tests -v

validate:
	python3 scripts/validate_catalog.py

audit-links:
	python3 scripts/audit_links.py
