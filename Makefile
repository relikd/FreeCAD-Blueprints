VERSION := $(shell sed -nE 's|.*<version>([^<]*).*|\1|p' package.xml)

release:
	git archive main --format zip --output "Blueprints-v$(VERSION).zip"
