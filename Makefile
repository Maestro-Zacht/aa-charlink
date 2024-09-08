tox_tests:
	python -m tox -v -e py311; \
	rm -rf .tox/

# Translation files
.PHONY: translations
translations:
	@echo "Creating or updating translation files"
	@django-admin makemessages \
		-l cs \
		-l de \
		-l es \
		-l fr_FR \
		-l it_IT \
		-l ja \
		-l ko_KR \
		-l nl \
		-l pl_PL \
		-l ru \
		-l sk \
		-l uk \
		-l zh_Hans \
		--keep-pot \
		--ignore 'build/*'

.PHONY: compile_translations
compile_translations:
	@echo "Compiling translation files"
	@django-admin compilemessages
