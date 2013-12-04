export PREFIX="/opt/canopsis"

.PHONY: all
all:
	@make -C widgets all

.PHONY: install
install: all
	@make -C widgets install
